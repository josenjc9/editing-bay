#!/usr/bin/env python3
"""從成片抽幾格，拼成一張分鏡板／接觸圖。

格數不固定，三種取法擇一：
  --times 1.3,9,17,25     指定秒數（有幾個就幾格；每段字出齊那格最有用）
  --count 8               在整支片裡平均抽 8 格
  --every 5               每 5 秒一格
用法：storyboard.py 成片.mp4 輸出.png --times 1.3,9,17 [--cols 3] [--width 330]
輸出圖的長邊不超過 1200 像素時才能直接讀。330 寬 × 3 欄 × 2 列剛好在範圍內；
格數多就調小 --width 或用更多 --cols。
"""
import shutil
import argparse, math, os, re, subprocess, sys, tempfile

FFMPEG = os.environ.get("FFMPEG", (shutil.which("ffmpeg") or "ffmpeg"))

ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("out")
g = ap.add_mutually_exclusive_group(required=True)
g.add_argument("--times")
g.add_argument("--count", type=int)
g.add_argument("--every", type=float)
ap.add_argument("--cols", type=int, default=3)
ap.add_argument("--width", type=int, default=330)
a = ap.parse_args()

def duration(path):
    out = subprocess.run([FFMPEG, "-hide_banner", "-i", path], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out)
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


if a.times:
    times = a.times.split(",")
else:
    dur = duration(a.video)
    if a.count:
        times = [f"{dur * (i + 0.5) / a.count:.2f}" for i in range(a.count)]
    else:
        times = [f"{t:.2f}" for t in [x * a.every for x in range(int(dur // a.every) + 1)] if t < dur]
n = len(times)
cols = min(a.cols, n)
rows = math.ceil(n / cols)
tmp = tempfile.mkdtemp(prefix="sb_")
files = []
for i, t in enumerate(times):
    p = os.path.join(tmp, f"{i:02d}.png")
    subprocess.run([FFMPEG, "-v", "error", "-y", "-ss", t, "-i", a.video, "-frames:v", "1",
                    "-vf", f"scale={a.width}:-1", p], check=True)
    files.append(p)
# 補空白格，讓每列一樣寬
w = h = None
probe = subprocess.run([FFMPEG, "-hide_banner", "-i", files[0]], capture_output=True, text=True).stderr
m = re.search(r"(\d+)x(\d+)", probe.split("Video:")[1]) if "Video:" in probe else None
w, h = (int(m.group(1)), int(m.group(2))) if m else (a.width, int(a.width * 16 / 9))
inputs, parts = [], []
for p in files:
    inputs += ["-i", p]
blank = rows * cols - n
for k in range(blank):
    inputs += ["-f", "lavfi", "-i", f"color=c=0xF5F0E4:s={w}x{h}"]
total = n + blank
rowlabels = []
for r in range(rows):
    idx = "".join(f"[{r * cols + c}]" for c in range(cols))
    parts.append(f"{idx}hstack={cols}[r{r}]" if cols > 1 else f"{idx}null[r{r}]")
    rowlabels.append(f"[r{r}]")
graph = ";".join(parts) + ";" + "".join(rowlabels) + (f"vstack={rows}" if rows > 1 else "null")
subprocess.run([FFMPEG, "-v", "error", "-y"] + inputs + ["-filter_complex", graph, "-frames:v", "1", a.out], check=True)
for p in files:
    os.remove(p)
os.rmdir(tmp)
print(f"分鏡板：{a.out}（{n} 格，{cols}×{rows}）")
