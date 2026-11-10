#!/usr/bin/env python3
"""切點連續性接觸圖：每個切點抽前後各 2 格（t-2f, t-1f, t, t+1f, t+2f），一個切點一列，由左到右。

用法：cuts_sheet.py 成片.mp4 輸出.png --times 5.2,9.8,14.0 [--width 220] [--fps 30]
  --times  切點秒數（換鏡後第一格的時間；可用 qa_video.py 偵測到的換鏡點，或鏡頭表算出的起點）
輸出圖長邊不超過 1200 像素才能直接讀：列數放不下時自動拆成 輸出_1.png、輸出_2.png…
用途：跨鏡頭連續性檢查（見 references/跨鏡頭連續性.md）。只備圖，不判斷；
方向、視線、動作相位、景別、光線由人逐張看。
"""
import shutil
import argparse, math, os, re, subprocess, tempfile

FFMPEG = os.environ.get("FFMPEG", (shutil.which("ffmpeg") or "ffmpeg"))
LIMIT = 1200

ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("out")
ap.add_argument("--times", required=True)
ap.add_argument("--width", type=int, default=220)
ap.add_argument("--fps", type=float)
a = ap.parse_args()

info = subprocess.run([FFMPEG, "-hide_banner", "-i", a.video], capture_output=True, text=True).stderr
if "Video:" not in info:
    raise SystemExit("讀不到影像串流：" + a.video)
fps = a.fps or float(re.search(r"([\d.]+) fps", info).group(1))
dm = re.search(r"Duration: (\d+):(\d+):([\d.]+)", info)
dur = int(dm.group(1)) * 3600 + int(dm.group(2)) * 60 + float(dm.group(3))
sz = re.search(r"Video:.*?, (\d{2,5})x(\d{2,5})", info)
vw, vh = int(sz.group(1)), int(sz.group(2))
cell_h = round(a.width * vh / vw)
rows_per = max(1, LIMIT // cell_h)
if 5 * a.width > LIMIT:
    raise SystemExit(f"5 格 × {a.width} 寬超過 {LIMIT}，請調小 --width")
times = [float(x) for x in a.times.split(",")]
bad = [t for t in times if t - 2 / fps < 0 or t + 2 / fps > dur]
if bad:
    raise SystemExit(f"切點離片頭／片尾不足 2 格，抽不出來：{bad}")

tmp = tempfile.mkdtemp(prefix="cuts_")
base, ext = os.path.splitext(a.out)
chunks = [times[i:i + rows_per] for i in range(0, len(times), rows_per)]
outs = []
for ci, chunk in enumerate(chunks):
    inputs, parts = [], []
    for ri, t in enumerate(chunk):
        for k in range(-2, 3):
            p = os.path.join(tmp, f"{ci}_{ri}_{k + 2}.png")
            subprocess.run([FFMPEG, "-v", "error", "-y", "-ss", f"{t + k / fps:.4f}", "-i", a.video,
                            "-frames:v", "1", "-vf", f"scale={a.width}:{cell_h}", p], check=True)
            inputs += ["-i", p]
        parts.append("".join(f"[{ri * 5 + c}]" for c in range(5)) + f"hstack=5[r{ri}]")
    n = len(chunk)
    graph = ";".join(parts) + ";" + "".join(f"[r{r}]" for r in range(n)) + (f"vstack={n}" if n > 1 else "null")
    out = a.out if len(chunks) == 1 else f"{base}_{ci + 1}{ext}"
    subprocess.run([FFMPEG, "-v", "error", "-y"] + inputs + ["-filter_complex", graph, "-frames:v", "1", out], check=True)
    outs.append(out)
    print(f"{out}：切點 {', '.join(f'{t:.2f}s' for t in chunk)}（每列 t-2f→t+2f，fps={fps:g}）")
for f in os.listdir(tmp):
    os.remove(os.path.join(tmp, f))
os.rmdir(tmp)
