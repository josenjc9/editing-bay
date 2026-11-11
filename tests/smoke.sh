#!/bin/bash
# 煙霧測試：用合成影片跑一遍 tools/ 與文件裡的 ffmpeg 指令。
# 用法：bash tests/smoke.sh        需要 ffmpeg、python3。
# 它只證明「指令與工具能跑、輸出規格正確」，不判斷畫面好不好看。
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TOOLS="$ROOT/skill/short-video-edit/tools"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
pass=0; fail=0
ok(){ echo "  ✓ $1"; pass=$((pass+1)); }
ng(){ echo "  ✗ $1"; fail=$((fail+1)); }
run(){ name="$1"; shift; if "$@" >"$T/log.txt" 2>&1; then ok "$name"; else ng "$name"; sed 's/^/      /' "$T/log.txt" | head -5; fi; }
ff(){ ffmpeg -v error -y "$@"; }

echo "== 準備合成素材"
ff -f lavfi -i testsrc=d=4:s=540x960:r=30 -f lavfi -i sine=d=4 -shortest -pix_fmt yuv420p "$T/a.mp4" && ok "a.mp4（含聲音）" || ng "a.mp4"
ff -f lavfi -i smptebars=d=4:s=540x960:r=30 -pix_fmt yuv420p "$T/b.mp4" && ok "b.mp4" || ng "b.mp4"
ff -f lavfi -i sine=d=4 "$T/sfx.wav"
ff -f lavfi -i smptebars=s=540x960 -frames:v 1 "$T/p.png"

echo "== tools/"
run "python 語法" python3 -I -m py_compile "$TOOLS"/*.py
run "shell 語法" bash -n "$TOOLS/deliver.sh" "$TOOLS/safe_trash.sh"
run "qa_video.py" python3 -I "$TOOLS/qa_video.py" "$T/a.mp4" "$T/qa" --size 540x960 --fps 30
run "storyboard.py" python3 -I "$TOOLS/storyboard.py" "$T/a.mp4" "$T/sb.png" --count 4
run "cuts_sheet.py" python3 -I "$TOOLS/cuts_sheet.py" "$T/a.mp4" "$T/cs.png" --times 2
ff -ss 1 -i "$T/a.mp4" -frames:v 1 "$T/shot.png"
run "find_frame.py" python3 -I "$TOOLS/find_frame.py" "$T/shot.png" "$T/a.mp4" "$T/b.mp4" --sdr
run "hf_lint.py（範例）" python3 -I "$TOOLS/hf_lint.py" "$ROOT/examples/transitions/index.html"
run "capcut_export.py 試跑（範例時間表）" python3 -I "$TOOLS/capcut_export.py" "$ROOT/examples/capcut-export-sample/spec.json" --dry-run
sed 's/clip_b.mp4/nope.mp4/' "$ROOT/examples/capcut-export-sample/spec.json" > "$ROOT/examples/capcut-export-sample/_bad.json"
if python3 -I "$TOOLS/capcut_export.py" "$ROOT/examples/capcut-export-sample/_bad.json" --dry-run >"$T/log.txt" 2>&1; then ng "capcut_export.py 缺素材應報錯"; else ok "capcut_export.py 缺素材會擋下"; fi
rm -f "$ROOT/examples/capcut-export-sample/_bad.json"
run "deliver.sh" bash "$TOOLS/deliver.sh" "$T/b.mp4" "$T/sfx.wav" smoke_test "$T/out"
mkdir -p "$T/home"; echo x > "$T/junk.txt"
run "safe_trash.sh" env HOME="$T/home" bash "$TOOLS/safe_trash.sh" "$T/junk.txt"

echo "== 技法庫的 ffmpeg 指令"
run "畫中畫" ff -i "$T/a.mp4" -i "$T/b.mp4" -filter_complex "[1]scale=180:-2[p];[0][p]overlay=W-w-20:H-h-100:enable='between(t,1,3)'" -an "$T/pip.mp4"
run "圓形小窗" ff -i "$T/a.mp4" -i "$T/b.mp4" -filter_complex "[1]scale=200:200:force_original_aspect_ratio=increase,crop=200:200,format=yuva420p,geq=lum='p(X,Y)':cb='p(X,Y)':cr='p(X,Y)':a='if(lte(hypot(X-100,Y-100),100),255,0)'[p];[0][p]overlay=W-w-20:H-h-100" -an "$T/pipr.mp4"
run "分割畫面" ff -i "$T/a.mp4" -i "$T/b.mp4" -filter_complex "[0]scale=270:960:force_original_aspect_ratio=increase,crop=270:960[l];[1]scale=270:960:force_original_aspect_ratio=increase,crop=270:960[r];[l][r]hstack" -an "$T/split.mp4"
run "定格" ff -i "$T/a.mp4" -vf "trim=0:2,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=1" -an "$T/freeze.mp4"
run "變速（三段）" ff -i "$T/a.mp4" -filter_complex "[0:v]split=3[a][b][c];[a]trim=0:1,setpts=PTS-STARTPTS[v1];[b]trim=1:2,setpts=(PTS-STARTPTS)*2[v2];[c]trim=2:4,setpts=PTS-STARTPTS[v3];[v1][v2][v3]concat=n=3:v=1:a=0" -an "$T/ramp.mp4"
run "整段變速含聲音" ff -i "$T/a.mp4" -filter_complex "[0:v]setpts=0.5*PTS[v];[0:a]atempo=2.0[a]" -map "[v]" -map "[a]" "$T/sp.mp4"
run "倒放" ff -i "$T/a.mp4" -vf "trim=0:2,setpts=PTS-STARTPTS,reverse" -an "$T/rev.mp4"
ff -i "$T/p.png" -vf "scale=1080:-2,zoompan=z='min(zoom+0.0015,1.3)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=90:s=540x960:fps=30,format=yuv420p" "$T/kb.mp4" 2>/dev/null
n="$(ffprobe -v error -select_streams v:0 -show_entries stream=nb_frames -of csv=p=0 "$T/kb.mp4" 2>/dev/null)"
[ "$n" = "90" ] && ok "Ken Burns（單張圖輸出 90 格）" || ng "Ken Burns（得到 ${n:-空} 格，應為 90）"
run "暗角切" ff -i "$T/a.mp4" -vf "eq=brightness=-0.4:enable='between(t,0.9,1.0)'" -an "$T/dip.mp4"
run "閃白" ff -i "$T/a.mp4" -vf "eq=brightness=0.6:enable='between(t,0.9,1.0)'" -an "$T/flash.mp4"
run "暗角加顆粒" ff -i "$T/a.mp4" -vf "vignette=angle=PI/8,noise=alls=8:allf=t" -an "$T/vg.mp4"

echo "== xfade 全部轉場類型"
bad=""; cnt=0
for t in $(ffmpeg -hide_banner -h filter=xfade 2>&1 | sed -n '/transition/,/duration/p' | grep -E "^\s+[a-z0-9]+\s+[0-9]+" | awk '{print $1}'); do
  cnt=$((cnt+1))
  ff -i "$T/a.mp4" -i "$T/b.mp4" -filter_complex "[0][1]xfade=transition=$t:duration=0.5:offset=3.5" -an "$T/x.mp4" 2>/dev/null || bad="$bad $t"
done
[ -z "$bad" ] && [ "$cnt" -gt 0 ] && ok "xfade $cnt 種轉場全部能出檔" || ng "xfade 失敗：$bad（共 $cnt 種）"

echo
echo "結果：$pass 通過，$fail 失敗"
[ "$fail" -eq 0 ]
