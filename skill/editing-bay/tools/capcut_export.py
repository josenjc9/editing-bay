#!/usr/bin/env python3
"""把「分軌時間表」(JSON) 寫成 CapCut（剪映國際版）草稿，帶去細修。

用途：AI 先把骨架剪好（輸出 B），細修在 CapCut 做；直出 mp4 是輸出 A，兩條路看這次要哪個。
這支只負責「依時間表放軌道」，不判斷剪輯好壞；畫面效果（遮罩聚焦、定位框、調色）不會重現，要在 CapCut 自己補。

需要：python3.9 以上，與第三方套件 pycapcut（`pip install pycapcut`，會一併裝 pymediainfo、imageio、numpy、Pillow；建議裝在獨立的虛擬環境，裝前請自己確認來源與授權、檢查這些套件的版本）。
  python3 capcut_export.py spec.json [--dry-run] [--drafts-dir 資料夾]
  `--dry-run` 只檢查時間表、列軌道統計，不需要安裝 pycapcut。

規矩（踩過的）：
- 輸出位置若在剪映自己的草稿目錄裡，寫之前 CapCut 必須完全退出（否則被覆蓋），程式會先檢查；寫到別的資料夾不受影響。
- CapCut 只連得到 ~/Movies 底下的素材：spec 的 media_dir 指到 ~/Movies/<名稱>，程式用 APFS 複製（cp -c，不佔額外空間）把素材放進去。
- 草稿寫進 spec 的 drafts_dir（預設 ~/CapCut草稿/），不寫進 CapCut 自己的草稿資料夾；要開時由使用者自己放入或匯入。
- 一律建新草稿，不覆寫既有同名草稿（同名就報錯）。

spec 格式見 examples/capcut_export_sample/spec.json（素材路徑相對於 spec 所在資料夾）。
"""
import json, os, subprocess, sys, shutil
from pathlib import Path

SEC = 1_000_000  # CapCut 內部單位：微秒


def die(msg):
    print('✖', msg); sys.exit(1)


def media_copy(src, media_dir, base):
    """把素材放進 ~/Movies 底下（APFS clone，不佔額外空間）；已經在裡面就原樣用。相對路徑以 spec 所在資料夾為準。"""
    src = os.path.expanduser(src)
    if not os.path.isabs(src): src = os.path.join(base, src)
    if not os.path.exists(src): die(f'找不到素材：{src}')
    movies = os.path.expanduser('~/Movies')
    if os.path.realpath(src).startswith(movies + os.sep): return src
    os.makedirs(media_dir, exist_ok=True)
    dst = os.path.join(media_dir, os.path.basename(src))
    if not os.path.exists(dst):
        r = subprocess.run(['cp', '-c', src, dst], capture_output=True, text=True)
        if r.returncode:  # 不在同一個 APFS 磁碟：退回一般複製（會佔空間）
            shutil.copy2(src, dst)
    return dst


def main():
    argv = sys.argv[1:]
    override = None
    if '--drafts-dir' in argv:
        i = argv.index('--drafts-dir'); override = argv[i + 1]; del argv[i:i + 2]
    args = [a for a in argv if not a.startswith('--')]
    dry = '--dry-run' in argv
    if len(args) != 1: die('用法：capcut_export.py spec.json [--dry-run] [--drafts-dir 資料夾]')
    spec = json.load(open(args[0], encoding='utf-8'))
    base = os.path.dirname(os.path.abspath(args[0]))
    for k in ('name', 'size', 'fps', 'tracks'):
        if k not in spec: die(f'spec 缺少欄位：{k}')
    # 先檢查所有素材都在，免得寫到一半失敗留下半成品草稿
    for tr in spec['tracks']:
        for s in tr['segments']:
            if 'src' in s:
                q = os.path.expanduser(s['src'])
                if not os.path.exists(q if os.path.isabs(q) else os.path.join(base, q)): die(f"找不到素材：{s['src']}")
    # 濾鏡名稱先驗證（試跑也驗），寫錯就在動手前報錯、列出相近名稱
    if True:
        _names = None
        for tr in spec['tracks']:
            for s in tr['segments']:
                f = s.get('filter')
                if not f: continue
                if tr['type'] != 'video': die('filter 只能放在 video 軌的片段上')
                if _names is None:
                    try: _names = set(n for n in dir(__import__('pycapcut').FilterType) if not n.startswith('_'))
                    except ImportError: _names = None
                nm = f.get('name') if isinstance(f, dict) else f
                if _names is not None and nm not in _names:
                    near = [n for n in sorted(_names) if str(nm).lower()[:3] in n.lower()][:8]
                    die(f"找不到濾鏡「{nm}」；相近的：{', '.join(near) or '（無）'}")
    # 只有「輸出位置在剪映自己的草稿目錄裡」才需要它完全退出；寫到別的資料夾不受影響
    _dd = os.path.realpath(os.path.expanduser(override or spec.get('drafts_dir', '~/CapCut草稿')))
    if not dry and 'com.lveditor.draft' in _dd and subprocess.run(['pgrep', '-x', 'CapCut'], capture_output=True).stdout.strip():
        die('輸出位置在剪映的草稿目錄裡，而 CapCut 還開著。請先完全退出再跑（寫草稿會被它覆蓋）。')

    cc = None if dry else __import__('pycapcut')   # 試跑不需要 pycapcut
    drafts_dir = os.path.expanduser(override or spec.get('drafts_dir', '~/CapCut草稿'))
    media_dir = os.path.expanduser(spec.get('media_dir', f"~/Movies/{spec['name']}"))
    W, H = spec['size']
    total = 0.0
    counts = {}
    if not dry:
        os.makedirs(drafts_dir, exist_ok=True)
        script = cc.DraftFolder(drafts_dir).create_draft(spec['name'], W, H, fps=spec['fps'], allow_replace=False)

    for tr in spec['tracks']:
        tname, ttype = tr['name'], tr['type']
        if ttype not in ('video', 'text', 'audio'): die(f'不支援的軌道類型：{ttype}')
        if not dry:
            script.add_track({'video': cc.TrackType.video, 'text': cc.TrackType.text, 'audio': cc.TrackType.audio}[ttype], tname)
        for i, s in enumerate(tr['segments']):
            at, dur = float(s['at']), float(s['dur'])
            if dur <= 0: die(f'{tname}[{i}] dur 必須 > 0')
            total = max(total, at + dur)
            counts[tname] = counts.get(tname, 0) + 1
            if dry: continue
            tgt = cc.trange(f'{at}s', f'{dur}s')
            if ttype in ('video', 'audio'):
                src = media_copy(s['src'], media_dir, base)
                kw = {}
                if 'in' in s: kw['source_timerange'] = cc.trange(f"{float(s['in'])}s", f"{dur * float(s.get('speed', 1.0))}s")
                if 'speed' in s and float(s['speed']) != 1.0: kw['speed'] = float(s['speed'])
                if 'volume' in s: kw['volume'] = float(s['volume'])
                if ttype == 'video':
                    seg = cc.VideoSegment(src, tgt, **kw)
                    if 'zoom' in s:   # [起始倍率, 結束倍率]：用縮放關鍵影格做數位推近
                        z0, z1 = s['zoom']
                        seg.add_keyframe(cc.KeyframeProperty.uniform_scale, 0, float(z0))
                        seg.add_keyframe(cc.KeyframeProperty.uniform_scale, f'{dur}s', float(z1))
                    for prop, val in (s.get('look') or {}).items():   # 調光：亮度／對比／飽和（-1～1，0＝原始）
                        seg.add_keyframe(getattr(cc.KeyframeProperty, prop), 0, float(val))
                    if s.get('filter'):   # 濾鏡：{"name": FilterType 名稱, "intensity": 0～100}；也可直接寫名稱字串
                        f = s['filter']; nm = f if isinstance(f, str) else f['name']
                        seg.add_filter(getattr(cc.FilterType, nm), 100.0 if isinstance(f, str) else float(f.get('intensity', 100)))
                else:
                    seg = cc.AudioSegment(src, tgt, **kw)
                    if 'fade' in s: seg.add_fade(f"{s['fade'][0]}s", f"{s['fade'][1]}s")
            else:
                st = cc.TextStyle(size=float(s.get('size', 5.0)), bold=bool(s.get('bold', True)),
                                  color=tuple(s.get('color', (1.0, 1.0, 1.0))), align=int(s.get('align', 0)))
                px, py = s.get('pos', [0.0, -0.8])
                seg = cc.TextSegment(s['text'], tgt, style=st, clip_settings=cc.ClipSettings(transform_x=px, transform_y=py))
                # 入場動畫是剪映的雲端資源，沒下載過會顯示「動畫遺失」；預設不放，要用請先在剪映確認該動畫已下載
                if s.get('intro'): seg.add_animation(getattr(cc.TextIntro, s['intro']))
            script.add_segment(seg, tname)

    if not dry: script.save()
    where = '（試跑，沒寫檔）' if dry else f"→ {drafts_dir}/{spec['name']}"
    print(f"✓ 草稿 {spec['name']} {W}x{H}@{spec['fps']} 總長 {total:.2f}s {where}")
    print('  軌道：' + '、'.join(f'{k} {v} 段' for k, v in counts.items()))
    if not dry: print(f'  素材放在 {media_dir}；要開時把草稿資料夾放進 CapCut 的草稿目錄。')


if __name__ == '__main__':
    main()
