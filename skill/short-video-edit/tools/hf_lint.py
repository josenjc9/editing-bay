#!/usr/bin/env python3
"""HyperFrames 組合頁（index.html）的地雷掃描。靜態查，不渲染；查的都是 skill 裡記過、或自查抓到過的坑。

用法：hf_lint.py index.html [更多.html ...]      結束碼：有 ERROR → 2；只有 WARN → 0

ERROR（會讓渲染壞掉或整支卡死）
  檔案被截斷（沒有 </html>、<script> 沒關）、沒有 window.__timelines
  最上層宣告重複（let／const 重複會語法錯誤；var／function 重複會靜默覆蓋，例如場景變數撞名 pul 讓影片從那鏡凍結）
  <video>／<audio> 缺 data-start／data-duration／data-track-index；<video> 缺 muted／playsinline
  tl.xxx('字面選擇器') 選不到任何元素（GSAP 靜默略過，動畫不會發生）；頁面有用 JS 建元素時降為 WARN
WARN（要回頭確認是不是有意）
  tl.set(選擇器,{opacity:1}) 之後又對同一選擇器 tl.from(…opacity:0)：from 的隱藏起點會被 set 蓋掉，出現→消失→再出現
  同一選擇器有多個 from／fromTo，後面的沒加 immediateRender:false（會把前面動畫的狀態在時間 0 蓋掉）
  字面選擇器一次選到多個元素、又沒有 stagger（只想動其中一個卻全動了，例如 '#s7 .win'）
  CSS font-size 小於 28px（影片字級下限；標籤／小字確認過可忽略）
  <video> 放在有 data-start 的外層元素裡，而不是根層直接子元素（透明影片 lint 會報 media_missing_data_start）
限制（要知道）
  只看「字面字串」選擇器；用函式參數、變數拼出來的選擇器（例如 typeIn(sel,…)）看不到。
  選擇器只支援 標籤、#id、.class 與「空白／>」組合；其他寫法略過不判斷。
  不查視覺、不查時間軸語意（字卡停留時間、節奏、色彩）；那些仍靠人看。
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}


class Node:
    def __init__(self, tag, attrs, parent):
        self.tag, self.attrs, self.parent, self.children = tag, dict(attrs), parent, []

    @property
    def classes(self):
        return (self.attrs.get('class') or '').split()


class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node('#doc', [], None)
        self.cur = self.root
        self.scripts, self.styles, self.script_lines = [], [], []
        self._buf, self._in = [], None

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs, self.cur)
        self.cur.children.append(n)
        if tag in ('script', 'style'):
            self._in, self._buf = tag, []
            if tag == 'script':
                self.script_lines.append(self.getpos()[0])
        if tag not in VOID:
            self.cur = n

    def handle_endtag(self, tag):
        if self._in == tag:
            (self.scripts if tag == 'script' else self.styles).append(''.join(self._buf))
            self._in = None
        n = self.cur
        while n and n.tag != tag:
            n = n.parent
        if n and n.parent:
            self.cur = n.parent

    def handle_data(self, data):
        if self._in:
            self._buf.append(data)


def walk(n):
    for c in n.children:
        yield c
        yield from walk(c)


def compound_match(n, comp):
    m = re.fullmatch(r'([a-zA-Z][\w-]*)?(?:#([\w-]+))?((?:\.[\w-]+)*)', comp)
    if not m or not comp:
        return None
    tag, idv, cls = m.group(1), m.group(2), [c for c in m.group(3).split('.') if c]
    return ((not tag or n.tag == tag) and (not idv or n.attrs.get('id') == idv)
            and all(c in n.classes for c in cls))


def select(tree, sel):
    """回傳符合的節點數；不支援的選擇器回傳 None。"""
    toks = re.findall(r'>|[^\s>]+', sel.strip())
    if not toks or toks[0] == '>' or toks[-1] == '>':
        return None
    parts, comb = [], []  # parts[i] 與 parts[i+1] 之間的連接子在 comb[i]
    for t in toks:
        if t == '>':
            comb.append('>')
        else:
            if len(parts) > len(comb):
                comb.append(' ')
            parts.append(t)
    for p in parts:
        if compound_match(Node('x', [], None), p) is None:
            return None

    def ok(n, i):
        if not compound_match(n, parts[i]):
            return False
        if i == 0:
            return True
        if comb[i - 1] == '>':
            return n.parent is not None and ok(n.parent, i - 1)
        a = n.parent
        while a is not None:
            if ok(a, i - 1):
                return True
            a = a.parent
        return False

    return sum(1 for n in walk(tree.root) if ok(n, len(parts) - 1))


def strip_js(src):
    """把註解和字串內容換成空白（保留字數與換行），方便掃括號與宣告。"""
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if src.startswith('//', i):
            j = src.find('\n', i)
            j = n if j < 0 else j
            out.append(' ' * (j - i)); i = j
        elif src.startswith('/*', i):
            j = src.find('*/', i + 2)
            j = n if j < 0 else j + 2
            out.append(re.sub(r'[^\n]', ' ', src[i:j])); i = j
        elif c in '\'"`':
            j = i + 1
            while j < n and src[j] != c:
                j += 2 if src[j] == '\\' else 1
            out.append(c + re.sub(r'[^\n]', ' ', src[i + 1:j]) + c); i = j + 1
        else:
            out.append(c); i += 1
    return ''.join(out)


def top_level_decls(src):
    clean = strip_js(src)
    depth = paren = 0
    found = []
    i = 0
    while i < len(clean):
        c = clean[i]
        if c == '{': depth += 1
        elif c == '}': depth -= 1
        elif c == '(': paren += 1
        elif c == ')': paren -= 1
        elif depth == 0 and paren == 0 and (i == 0 or not re.match(r'[\w$.]', clean[i - 1])):
            m = re.match(r'(const|let|var)\s+([A-Za-z_$][\w$]*)', clean[i:])
            if m:
                found.append((m.group(1), m.group(2), clean.count('\n', 0, i) + 1))
            else:
                m = re.match(r'function\s+([A-Za-z_$][\w$]*)', clean[i:])
                if m:
                    found.append(('function', m.group(1), clean.count('\n', 0, i) + 1))
        i += 1
    return found


def split_args(s):
    args, depth, cur = [], 0, []
    for c in s:
        if c in '([{': depth += 1
        elif c in ')]}': depth -= 1
        if c == ',' and depth == 0:
            args.append(''.join(cur).strip()); cur = []
        else:
            cur.append(c)
    if cur:
        args.append(''.join(cur).strip())
    return args


def tl_calls(src):
    """找出 tl.set／from／to／fromTo 呼叫，回傳 (方法, 參數列, 行號)。"""
    clean = strip_js(src)
    calls = []
    for m in re.finditer(r'\b\w+\s*\.\s*(set|from|to|fromTo)\s*\(', clean):
        i, depth = m.end(), 1
        while i < len(clean) and depth:
            depth += {'(': 1, ')': -1}.get(clean[i], 0)
            i += 1
        # 用原文取參數（字串內容要保留，選擇器在裡面）
        calls.append((m.group(1), split_args(src[m.end():i - 1]), clean.count('\n', 0, m.start()) + 1))
    return calls


def lint(path):
    res = []

    def add(level, line, msg):
        res.append((level, line, msg))

    html = Path(path).read_text(encoding='utf-8', errors='replace')
    if not re.search(r'</html>\s*$', html, re.I):
        add('ERROR', 0, '檔尾沒有 </html>，檔案可能被截斷')
    t = Tree()
    t.feed(html)
    if html.lower().count('<script') != html.lower().count('</script'):
        add('ERROR', 0, '<script> 與 </script> 數量不一致')
    js = '\n'.join(t.scripts)
    dynamic = bool(re.search(r'createElement|innerHTML|insertAdjacentHTML', js))
    if '__timelines' not in js:
        add('ERROR', 0, '找不到 window.__timelines')

    # 最上層宣告重複
    seen = {}
    decls = [(k, nm, ln + off - 1) for src, off in zip(t.scripts, t.script_lines) for k, nm, ln in top_level_decls(src)]
    for kind, name, ln in decls:
        if name in seen:
            level = 'ERROR'
            add(level, ln, f'最上層「{name}」重複宣告（{seen[name][0]} 在第 {seen[name][1]} 行，這裡是 {kind}）：'
                          f'{"let／const 會語法錯誤" if "let" in (kind, seen[name][0]) or "const" in (kind, seen[name][0]) else "後者靜默覆蓋前者"}')
        else:
            seen[name] = (kind, ln)

    # 媒體元素
    root = next((n for n in walk(t.root) if 'data-composition-id' in n.attrs), None)
    for n in walk(t.root):
        if n.tag in ('video', 'audio'):
            label = f'<{n.tag} id={n.attrs.get("id", "?")}>'
            miss = [a for a in ('data-start', 'data-duration', 'data-track-index') if a not in n.attrs]
            if miss:
                add('ERROR', 0, f'{label} 缺 {", ".join(miss)}')
            if n.tag == 'video':
                miss = [a for a in ('muted', 'playsinline') if a not in n.attrs]
                if miss:
                    add('ERROR', 0, f'{label} 缺 {", ".join(miss)}')
                a = n.parent
                if root is not None and n.parent is not root:
                    while a is not None and a is not root:
                        if 'data-start' in a.attrs:
                            add('WARN', 0, f'{label} 放在帶 data-start 的外層元素裡，要改成根層直接子元素')
                            break
                        a = a.parent

    # 時間軸呼叫
    calls = [(m, a, ln + off - 1) for src, off in zip(t.scripts, t.script_lines) for m, a, ln in tl_calls(src)]
    by_sel = {}
    for method, args, ln in calls:
        if not args:
            continue
        m = re.fullmatch(r'''(['"])(.+)\1''', args[0].strip())
        if not m:
            continue
        sel = m.group(2)
        body = ' '.join(args[1:])
        by_sel.setdefault(sel, []).append((method, args, ln, body))
        cnt = select(t, sel)
        if cnt == 0:
            if dynamic:
                add('WARN', ln, f'選擇器 {sel!r} 在 HTML 裡選不到；本頁用 JS 動態建立元素，確認它真的會被建出來')
            else:
                add('ERROR', ln, f'選擇器 {sel!r} 選不到任何元素（GSAP 靜默略過，動畫不會發生）')
        elif cnt and cnt > 1 and 'stagger' not in body and method != 'set':
            add('WARN', ln, f'選擇器 {sel!r} 選到 {cnt} 個元素、沒有 stagger——是要全部一起動嗎？只想動一個就改用 id')

    for sel, lst in by_sel.items():
        sets_on = [x for x in lst if x[0] == 'set' and re.search(r'opacity\s*:\s*1\b', x[3])]
        for s_ in sets_on:
            for f in lst:
                if f[0] in ('from', 'fromTo') and f[2] > s_[2] and re.search(r'opacity\s*:\s*0\b', f[3]):
                    add('WARN', f[2], f'{sel!r}：第 {s_[2]} 行 set opacity:1，後面第 {f[2]} 行又 from opacity:0——'
                                      f'from 的隱藏起點會被 set 蓋掉（要隱藏就 set 0、用 to 顯示）')
                    break
        froms = [x for x in lst if x[0] in ('from', 'fromTo')]
        for later in froms[1:]:
            if 'immediateRender' not in later[3]:
                add('WARN', later[2], f'{sel!r} 有多個 from／fromTo，這個沒加 immediateRender:false（會在時間 0 蓋掉前面動畫的狀態）')

    # CSS 字級
    for css in t.styles:
        for rule in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
            for fs in re.finditer(r'font-size\s*:\s*(\d+(?:\.\d+)?)px', rule.group(2)):
                if float(fs.group(1)) < 28:
                    add('WARN', 0, f'CSS {rule.group(1).strip()[:40]!r} font-size {fs.group(1)}px < 28px（影片字級下限）')
    return res


def main():
    files = sys.argv[1:]
    if not files:
        print(__doc__)
        sys.exit(1)
    bad = False
    for f in files:
        if not Path(f).exists():
            print(f'找不到：{f}')
            sys.exit(1)
        res = lint(f)
        print(f'== {f}：{sum(r[0] == "ERROR" for r in res)} ERROR，{sum(r[0] == "WARN" for r in res)} WARN')
        for level, ln, msg in sorted(res, key=lambda r: (r[0] != 'ERROR', r[1])):
            print(f'  [{level}]{f" L{ln}" if ln else ""} {msg}')
        bad = bad or any(r[0] == 'ERROR' for r in res)
    print('只做靜態檢查；字面選擇器以外的寫法看不到，畫面與節奏仍要渲染後逐格看。')
    sys.exit(2 if bad else 0)


if __name__ == '__main__':
    main()
