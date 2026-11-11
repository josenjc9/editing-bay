#!/usr/bin/env python3
"""成片機檢：任何 mp4 都能跑（不需要 shots.json）。只核數字、備圖；畫面好不好看仍由人逐張看。

用法：qa_video.py 成片.mp4 輸出資料夾 [--size 1080x1920] [--fps 30] [--share 分享版.mp4]
                  [--compare 另一支.mp4] [--scene 0.04]
產出（輸出資料夾）：
  frames/xf_<序>_<時間>_{before,after}.jpg   每個偵測到的換鏡點，前後各一格
  report.json                                 數字結果
檢查項（FAIL 結束碼 2，WARN 只列出）：
  解析度／fps 與指定值一致、總長為整數幀、實際解碼幀數＝總長×fps
  有聲軌、聲軌長度與影片長度差 ≤0.1 秒（舊的短 sfx 會把成片截斷）
  最大音量 <-0.5dB（貼近 0dB 判爆音）、整體響度（LUFS）列出
  黑畫面段（>0.3 秒）、凍結段（>1 秒沒有任何畫面變化，例如腳本丟錯整支卡死）
  分享版 ≤9MB
  --compare：兩支影片在 12 個等距時間點的畫面雜湊是否一致（可重現檢查：同一份原始碼渲染兩次）
限制：換鏡偵測用畫面差異門檻（預設 0.04，滑動轉場分數約 0.06～0.10；硬切會高很多，內容動態大的片可能多抓，調高 --scene）；
淡入淡出若分數低於門檻會漏。凍結＝連續 1 秒以上與前一格幾乎逐像素相同（雜訊門檻 -80dB），畫面中細微的呼吸起伏這種小動態不算凍結。
"""
import os
import shutil
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

FFMPEG = os.environ.get("FFMPEG", shutil.which("ffmpeg") or "ffmpeg")
SHARE_MAX = 9 * 1000 * 1000


def run(args):
    return subprocess.run([FFMPEG, '-hide_banner', *args], capture_output=True, text=True)


def info(video):
    err = run(['-i', str(video)]).stderr
    vline = re.search(r'Stream #\S+.*Video:.*', err)
    v = re.search(r', (\d{2,5})x(\d{2,5})', vline.group(0)) if vline else None
    f = re.search(r'([\d.]+) fps', vline.group(0)) if vline else None
    d = re.search(r'Duration: (\d+):(\d+):([\d.]+)', err)
    a = re.search(r'Stream #\S+.*Audio:', err)
    dur = int(d.group(1)) * 3600 + int(d.group(2)) * 60 + float(d.group(3)) if d else None
    return dict(
        size=(int(v.group(1)), int(v.group(2))) if v else None,
        fps=float(f.group(1)) if f else None,
        duration=dur,
        has_audio=bool(a),
    )


def decoded_frames(video):
    err = run(['-i', str(video), '-map', '0:v:0', '-f', 'null', '-']).stderr
    n = re.findall(r'frame=\s*(\d+)', err)
    return int(n[-1]) if n else None


def audio_stats(video):
    err = run(['-i', str(video), '-map', '0:a:0', '-af', 'volumedetect,ebur128=framelog=quiet', '-f', 'null', '-']).stderr
    mx = re.search(r'max_volume: ([-0-9.]+) dB', err)
    lufs = re.findall(r'I:\s+([-0-9.]+) LUFS', err)
    return (float(mx.group(1)) if mx else None), (float(lufs[-1]) if lufs else None)


def audio_duration(video):
    err = run(['-i', str(video), '-map', '0:a:0', '-f', 'null', '-']).stderr
    t = re.findall(r'time=(\d+):(\d+):([\d.]+)', err)
    if not t:
        return None
    h, m, s = t[-1]
    return int(h) * 3600 + int(m) * 60 + float(s)


def segments(video, vf, key_start, key_end):
    err = run(['-i', str(video), '-vf', vf, '-an', '-f', 'null', '-']).stderr
    starts = [float(x) for x in re.findall(key_start + r':\s*([\d.]+)', err)]
    ends = [float(x) for x in re.findall(key_end + r':\s*([\d.]+)', err)]
    return starts, ends


def scene_times(video, thr):
    """回傳換鏡區段 [(起, 迄)]：分數 >thr 的相鄰格（間隔 ≤0.5 秒）併成一段，滑動轉場才不會被切成好幾個點。"""
    err = run(['-i', str(video), '-an', '-vf', f"select='gt(scene,{thr})',showinfo", '-f', 'null', '-']).stderr
    pts = [float(x) for x in re.findall(r'pts_time:([\d.]+)', err)]
    runs = []
    for t in pts:
        if runs and t - runs[-1][1] <= 0.5:
            runs[-1][1] = t
        else:
            runs.append([t, t])
    return [tuple(r) for r in runs]


def grab(video, t, out):
    r = run(['-v', 'error', '-y', '-ss', f'{max(t, 0):.3f}', '-i', str(video), '-frames:v', '1', '-q:v', '2', str(out)])
    return r.returncode == 0 and Path(out).exists()


def frame_hash(video, t):
    r = subprocess.run([FFMPEG, '-v', 'error', '-ss', f'{t:.3f}', '-i', str(video), '-frames:v', '1',
                        '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True)
    return hashlib.md5(r.stdout).hexdigest() if r.stdout else None


def main():
    pos, opts, argv, k = [], {}, sys.argv[1:], 0
    while k < len(argv):
        if argv[k].startswith('--') and k + 1 < len(argv):
            opts[argv[k][2:]] = argv[k + 1]
            k += 2
        else:
            pos.append(argv[k])
            k += 1
    if len(pos) < 2:
        print(__doc__)
        sys.exit(1)
    video, out = Path(pos[0]), Path(pos[1])
    if not video.exists():
        print(f'找不到影片：{video}')
        sys.exit(1)
    (out / 'frames').mkdir(parents=True, exist_ok=True)

    res = []  # (level, rule, msg)

    def add(level, rule, msg):
        res.append((level, rule, msg))
        print(f'[{level}] {rule}: {msg}')

    i = info(video)
    if not i['size'] or not i['duration'] or not i['fps']:
        add('FAIL', '讀檔', '讀不到影片資訊')
        sys.exit(2)
    w, h = i['size']
    fps, dur = i['fps'], i['duration']
    print(f'{video.name}: {w}x{h} {fps}fps {dur:.2f}s 聲軌={"有" if i["has_audio"] else "無"}')

    if 'size' in opts:
        ew, eh = (int(x) for x in opts['size'].lower().split('x'))
        if (w, h) != (ew, eh):
            add('FAIL', '解析度', f'實際 {w}x{h}，預期 {ew}x{eh}')
    exp_fps = float(opts['fps']) if 'fps' in opts else None
    if exp_fps and abs(fps - exp_fps) > 0.01:
        add('FAIL', 'fps', f'實際 {fps}，預期 {exp_fps}')

    nf = decoded_frames(video)
    exp_n = dur * fps
    if nf is None:
        add('WARN', '幀數', '讀不到實際解碼幀數')
    else:
        # Duration 只到 0.01 秒，容許 ±1 幀的四捨五入
        if abs(nf - round(exp_n)) > 1:
            add('FAIL', '幀數', f'解碼 {nf} 幀，總長×fps≈{exp_n:.1f}')
        if abs(exp_n - round(exp_n)) > 0.6:
            add('WARN', '整數幀', f'總長×fps={exp_n:.2f} 不是整數幀（常見的幀數差 1 原因）')

    if not i['has_audio']:
        add('WARN', '聲軌', '沒有聲軌（廣告片預設只要音效，確認是有意為之）')
    else:
        mx, lufs = audio_stats(video)
        if mx is not None and mx > -0.5:
            add('FAIL', '爆音', f'最大音量 {mx} dB，貼近 0dB')
        print(f'  最大音量 {mx} dB，整體響度 {lufs} LUFS')
        ad = audio_duration(video)
        if ad is not None and abs(ad - dur) > 0.1:
            add('FAIL', '聲軌長度', f'聲軌 {ad:.2f}s ≠ 影片 {dur:.2f}s（舊的短 sfx 會把成片截斷）')

    bs, be = segments(video, 'blackdetect=d=0.3:pix_th=0.05', 'black_start', 'black_end')
    for s, e in zip(bs, be):
        add('WARN', '黑畫面', f'{s:.2f}s–{e:.2f}s 整片近乎全黑（黑色主體用 zoomin 轉場會這樣）')
    fs, fe = segments(video, 'freezedetect=n=-80dB:d=1', 'lavfi.freezedetect.freeze_start', 'lavfi.freezedetect.freeze_end')
    for k, s in enumerate(fs):
        e = fe[k] if k < len(fe) else dur
        add('WARN', '凍結', f'{s:.2f}s–{e:.2f}s 畫面逐像素幾乎沒變（有意停格以外，可能是腳本錯誤卡死）')

    thr = float(opts.get('scene', 0.04))
    ts = scene_times(video, thr)
    for k, (t0, t1) in enumerate(ts):
        grab(video, t0 - 0.12, out / 'frames' / f'xf_{k:02d}_{t0:.2f}_before.jpg')
        grab(video, t1 + 0.12, out / 'frames' / f'xf_{k:02d}_{t0:.2f}_after.jpg')
    print(f'  偵測到 {len(ts)} 個換鏡點（門檻 {thr}），前後格在 {out / "frames"}')

    if 'share' in opts:
        sz = Path(opts['share']).stat().st_size
        if sz > SHARE_MAX:
            add('FAIL', '分享版大小', f'{sz / 1e6:.2f}MB > 9MB')
        else:
            print(f'  分享版 {sz / 1e6:.2f}MB ≤ 9MB')

    if 'compare' in opts:
        other = Path(opts['compare'])
        times = [dur * (k + 0.5) / 12 for k in range(12)]
        diff = [t for t in times if frame_hash(video, t) != frame_hash(other, t)]
        if diff:
            add('FAIL', '可重現', f'{len(diff)}/12 個時間點畫面不同：' + ', '.join(f'{t:.1f}s' for t in diff))
        else:
            print('  可重現：12 個時間點畫面雜湊全部一致')

    (out / 'report.json').write_text(json.dumps(dict(
        video=str(video), size=[w, h], fps=fps, duration=dur, frames=nf, scenes=ts,
        results=[dict(level=a, rule=b, msg=c) for a, b, c in res]), ensure_ascii=False, indent=1))
    fails = [r for r in res if r[0] == 'FAIL']
    print(f'結果：{len(fails)} FAIL，{len(res) - len(fails)} WARN；圖要逐張看，這支不判斷視覺。')
    sys.exit(2 if fails else 0)


if __name__ == '__main__':
    main()
