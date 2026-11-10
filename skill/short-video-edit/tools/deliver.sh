#!/bin/bash
# 合音效、壓輕量版、複製到交付資料夾、md5 核對、量長度與最大音量。
#
# 用法：deliver.sh <無聲影片.mp4> <音效.wav> <片名_秒數> <輸出資料夾> [crf，預設 20]
# 例：  deliver.sh out/silent.mp4 sfx.wav my_video_37s "$HOME/Videos/my-project/final"
# 會產出（輸出資料夾裡）：<片名>.mp4 與 <片名>_輕量版.mp4。已存在的同名檔不會被覆蓋——先用 safe_trash.sh 移走。
# 不會做的事：不清舊版、不寫定稿圖表（那些要等使用者點頭）。
set -eu   # 不開 pipefail：下面量長度／音量的管線用 head -1，會讓上游被提早關閉而誤判失敗

FFMPEG="${FFMPEG:-ffmpeg}"
# macOS 用 md5 -q，Linux 用 md5sum
md5f(){ if command -v md5 >/dev/null 2>&1; then md5 -q "$1"; else md5sum "$1" | cut -d" " -f1; fi; }
[ $# -ge 4 ] || { sed -n 2,7p "$0"; exit 1; }
SILENT="$1"; SFX="$2"; NAME="$3"; OUT="$4"; CRF="${5:-20}"
case "$NAME" in */*|*..*|-*|"") echo "片名不可含 / 或 .. 或以 - 開頭"; exit 1;; esac
case "$CRF" in ''|*[!0-9]*) echo "crf 必須是數字"; exit 1;; esac
[ -f "$SILENT" ] || { echo "找不到影片：$SILENT"; exit 1; }
[ -f "$SFX" ] || { echo "找不到音效：$SFX"; exit 1; }
mkdir -p "$OUT"
for f in "$OUT/$NAME.mp4" "$OUT/${NAME}_輕量版.mp4"; do
  [ ! -e "$f" ] || { echo "已存在，不覆蓋：${f}（先用 safe_trash.sh 移走舊的）"; exit 1; }
done

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
"$FFMPEG" -v error -y -i "$SILENT" -i "$SFX" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest "$TMP/full.mp4"
"$FFMPEG" -v error -y -i "$TMP/full.mp4" -c:v libx264 -crf "$CRF" -preset slow -c:a copy "$TMP/light.mp4"

DUR="$("$FFMPEG" -hide_banner -i "$TMP/full.mp4" 2>&1 | grep -o 'Duration: [0-9:.]*' | head -1 || true)"
MAXV="$("$FFMPEG" -hide_banner -i "$TMP/full.mp4" -af volumedetect -f null - 2>&1 | grep -o 'max_volume: [-0-9.]* dB' | head -1 || true)"
cp "$TMP/full.mp4" "$OUT/$NAME.mp4"; cp "$TMP/light.mp4" "$OUT/${NAME}_輕量版.mp4"
A="$(md5f "$TMP/full.mp4")"; B="$(md5f "$OUT/$NAME.mp4")"
C="$(md5f "$TMP/light.mp4")"; D="$(md5f "$OUT/${NAME}_輕量版.mp4")"
[ "$A" = "$B" ] && [ "$C" = "$D" ] || { echo "md5 對不上，複製有問題"; exit 2; }

echo "完成：$OUT"
echo "  $NAME.mp4            $(du -h "$OUT/$NAME.mp4" | cut -f1)"
echo "  ${NAME}_輕量版.mp4    $(du -h "$OUT/${NAME}_輕量版.mp4" | cut -f1)"
echo "  $DUR   $MAXV   md5 核對：一致"
# 最大音量接近 0dB 要小心爆音
case "$MAXV" in *"-0."*|*" 0.0"*) echo "  ⚠ 最大音量貼近 0dB，可能爆音";; esac
