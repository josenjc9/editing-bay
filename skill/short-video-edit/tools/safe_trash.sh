#!/bin/bash
# 把檔案或資料夾移到垃圾桶（不是直接刪）。同名不會被靜默略過——一律加時間前綴，並逐個印出結果。
# 起因：曾用 `mv -n` 移舊版，垃圾桶已有同名檔時它「靜默不移」，舊版還留在原地沒人發現。
#
# 用法：safe_trash.sh <檔案或資料夾> [...]
# 沒有的路徑會報錯並結束碼 1；其他照常處理。不會清空垃圾桶。
set -u
[ $# -ge 1 ] || { sed -n 2,6p "$0"; exit 1; }
TS="$(date +%Y%m%d_%H%M%S)"
rc=0
for p in "$@"; do
  if [ ! -e "$p" ]; then echo "✗ 不存在：$p"; rc=1; continue; fi
  base="$(basename "$p")"
  dest="$HOME/.Trash/${TS}_${base}"
  [ ! -e "$dest" ] || dest="$HOME/.Trash/${TS}_${RANDOM}_${base}"   # 同一秒同名也不蓋掉前一個
  if mv -- "$p" "$dest" 2>/dev/null; then
    [ -e "$dest" ] && [ ! -e "$p" ] && echo "✓ $p → 垃圾桶/${TS}_${base}" || { echo "✗ 移動後狀態不對：$p"; rc=1; }
  else
    echo "✗ 移動失敗：$p"; rc=1
  fi
done
exit $rc
