#!/usr/bin/env python3
"""收到使用者傳來的截圖時，找出它是哪支素材（或成片）的第幾秒。

把截圖和每支影片逐格縮成 36×64 灰階，算平均平方差，列最像的前幾名。
iPhone HLG 素材會先轉 SDR 再比；成片（已是 SDR）加 --sdr。
截圖若帶播放器邊框，用 --crop 指定只取中間畫面（預設取寬度中間 62%，對直式手機截圖剛好）。

用法：find_frame.py 截圖.png 影片1 [影片2 ...] [--fps 10] [--sdr] [--crop 0.62] [--top 6]
例：  find_frame.py shot.png clips/a.mov clips/b.mov clips/c.mov
限制：差值是相對比較，數字本身沒有門檻；第一名明顯低於其他影片才可信。畫面很像的連續格會排在一起。
"""
import shutil
import argparse, os, subprocess

FF = os.environ.get("FFMPEG", shutil.which("ffmpeg") or "ffmpeg")
TM = ('zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,'
      'zscale=t=bt709:m=bt709:r=tv,format=yuv420p,')
W, H = 36, 64

ap = argparse.ArgumentParser()
ap.add_argument("shot")
ap.add_argument("videos", nargs="+")
ap.add_argument("--fps", type=float, default=10)
ap.add_argument("--sdr", action="store_true", help="影片已是 SDR（例如成片），不做 HLG 轉換")
ap.add_argument("--crop", type=float, default=0.62, help="截圖取寬度中間多少比例")
ap.add_argument("--top", type=int, default=6)
a = ap.parse_args()


def grab(args, vf):
    r = subprocess.run([FF, "-v", "error"] + args + ["-vf", vf + f"scale={W}:{H},format=gray", "-f", "rawvideo", "-"],
                       capture_output=True)
    if r.returncode != 0:
        raise SystemExit(f"讀取失敗：{args[-1]}\n{r.stderr.decode()[-300:]}")
    return r.stdout


c = a.crop
ref = grab(["-i", a.shot], f"crop=iw*{c}:ih*0.98:iw*{(1-c)/2}:0,")
best = []
for v in a.videos:
    raw = grab(["-i", v], ("" if a.sdr else TM) + f"fps={a.fps},")
    n = len(raw) // (W * H)
    for i in range(n):
        f = raw[i * W * H:(i + 1) * W * H]
        best.append((sum((x - y) ** 2 for x, y in zip(f, ref)) / (W * H), v.split("/")[-1], i / a.fps))
best.sort()
for d, name, t in best[:a.top]:
    print(f"{d:8.0f}  {name}  {t:.1f} 秒")
