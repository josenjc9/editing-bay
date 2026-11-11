#!/usr/bin/env python3
"""成片文字 vs 原圖／原稿：用文字辨識逐句核對。

用法：
  ocr_check.py --video 成片.mp4 --times 1.3,9.1,17.1 --source 原圖1.png 原圖2.png --expect 預期句子.txt

做三件事：
  1. 每句預期文字（expect 檔一行一句）要「同時」出現在原圖和成片畫面上；沒對上的列出來（結束碼 2）。
  2. 成片畫面上有、但原圖沒有的文字行（長度 ≥ 4、相鄰兩字組合覆蓋率 < 80%）也列出來——這是「我自己加的字」，要逐條確認 使用者給過。
  3. 辨識誤差已知的字（麽→麼、©、| 等）先做對照表，不會誤報；使用者另外給過的字用 --allow 檔放行。

重要限制（寫在這裡）：
  - 文字對得上 ≠ 內容正確。內容正確性要另外查來源（見 SKILL.md 關卡 1）。
  - 辨識會漏讀、錯讀；沒對上的句子一定要回頭看原圖／畫面，不要直接判錯或判對。
  - 只核「抽到的那幾格」，沒抽到的畫面沒核。times 要涵蓋每段字出齊的那一格。
"""
import shutil
import argparse, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FFMPEG = os.environ.get("FFMPEG", (shutil.which("ffmpeg") or "ffmpeg"))
SWIFT_SRC = os.path.join(HERE, "ocr.swift")
BIN = os.path.join(HERE, "bin", "ocr")

# 已知辨識誤差：比對前先換成同一個字
ALIAS = {"麽": "麼", "©": "", "®": "", "|": "", "｜": ""}
PUNCT = r"[\s，。、：:；;？?！!\-－—~～·・\"“”‘’（）()\[\]/「」『』.,]"


def norm(s: str) -> str:
    for a, b in ALIAS.items():
        s = s.replace(a, b)
    return re.sub(PUNCT, "", s)


def build_ocr():
    if os.path.exists(BIN) and os.path.getmtime(BIN) >= os.path.getmtime(SWIFT_SRC):
        return
    os.makedirs(os.path.dirname(BIN), exist_ok=True)
    r = subprocess.run(["swiftc", "-O", SWIFT_SRC, "-o", BIN], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("編譯 ocr.swift 失敗：\n" + r.stderr[-800:])


def ocr(paths):
    r = subprocess.run([BIN] + paths, capture_output=True, text=True)
    out, cur = {}, None
    for line in r.stdout.splitlines():
        if line.startswith("## "):
            cur = line[3:]
            out[cur] = []
        elif cur is not None and line.strip():
            out[cur].append(line)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--times", required=True, help="要抽的秒數，逗號分隔")
    ap.add_argument("--source", nargs="+", required=True, help="原圖（可多張）")
    ap.add_argument("--expect", required=True, help="預期句子檔，一行一句")
    ap.add_argument("--allow", help="使用者另外給過的字（一行一句）：成片有、原圖沒有的文字行，若含這些就不列出")
    ap.add_argument("--keep", help="把抽出的畫面留在這個資料夾（預設用完刪掉）")
    a = ap.parse_args()

    build_ocr()
    work = a.keep or tempfile.mkdtemp(prefix="ocrcheck_")
    os.makedirs(work, exist_ok=True)
    frames = []
    for i, t in enumerate(a.times.split(","), 1):
        p = os.path.join(work, f"v{i}_{t}.png")
        subprocess.run([FFMPEG, "-v", "error", "-y", "-ss", t, "-i", a.video, "-frames:v", "1", p], check=True)
        frames.append(p)

    vid = ocr(frames)
    src = ocr(a.source)
    vlines = [l for ls in vid.values() for l in ls]
    slines = [l for ls in src.values() for l in ls]
    V, S = norm("".join(vlines)), norm("".join(slines))

    expect = [l.strip() for l in open(a.expect, encoding="utf-8") if l.strip() and not l.startswith("#")]
    bad = []
    for e in expect:
        n = norm(e)
        in_v, in_s = n in V, n in S
        if not (in_v and in_s):
            bad.append((e, in_s, in_v))
    print(f"預期 {len(expect)} 句；同時出現在原圖與成片：{len(expect) - len(bad)} 句")
    for e, in_s, in_v in bad:
        print(f"  ✗ {e}   原圖:{'有' if in_s else '無'}  成片:{'有' if in_v else '無'}   ← 回頭看畫面／原圖，可能是辨識誤差")

    allow = []
    if a.allow:
        allow = [norm(l) for l in open(a.allow, encoding="utf-8") if l.strip() and not l.startswith("#")]
    sbi = {S[i:i + 2] for i in range(len(S) - 1)}

    def covered(n):
        """這行字的相鄰兩字組合有 80% 以上出現在原圖文字裡 → 視為原圖已有（辨識亂序、多讀一個字都不列）。"""
        bi = [n[i:i + 2] for i in range(len(n) - 1)]
        return bool(bi) and sum(b in sbi for b in bi) / len(bi) >= 0.8

    extra = []
    for l in vlines:
        n = norm(l)
        if len(n) >= 4 and n not in S and not covered(n) and not re.fullmatch(r"[0-9A-Za-z/]+", n):
            if any(x in n or n in x for x in allow):
                continue
            extra.append(l)
    print(f"\n成片畫面有、原圖沒有的文字行（{len(extra)} 條，請確認每條都是 使用者給過的）：")
    for l in extra:
        print("  ·", l)
    if not a.keep:
        for f in frames:
            os.remove(f)
        os.rmdir(work)
    sys.exit(2 if bad else 0)


if __name__ == "__main__":
    main()
