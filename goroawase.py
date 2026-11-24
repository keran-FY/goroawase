#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""goroawase —— 数字谐音的编码与解码。日语 + 中文。

日语（語呂合わせ）：把数字逐个读成假名，再拼成词。
    0→お/れ/ぜ   1→い/ひ   2→に/ふ   3→さ/み   4→し/よ
    5→ご/こ     6→ろ/む   7→な      8→は/や   9→く/き
    所以 0721 → お・な・に・い → オナニー；4649 → よろしく。

中文：不是逐字读，是**整段当拼音缩写**用。
    520 → 我爱你   1314 → 一生一世   886 → 拜拜咯   7456 → 气死我了
    所以中文这边要的是"怎么切段"，不是"怎么逐位替换"。

用法：
    python goroawase.py 0721              # 日语：这个数字串能读成什么
    python goroawase.py 4649 --all        # 日语：列出全部组合
    python goroawase.py --to よろしく       # 日语：反查数字
    python goroawase.py --zh 5201314      # 中文：切成词
    python goroawase.py --zh-to 我爱你      # 中文：反查数字
"""
import argparse
import json
import os
import sys

# ---------------------------------------------------------------- 日语表
READINGS = {
    "0": ["お", "れ", "ぜ", "わ"],
    "1": ["い", "ひ", "ひと"],
    "2": ["に", "ふ", "じ"],
    "3": ["さ", "み", "さん"],
    "4": ["し", "よ", "よん"],
    "5": ["ご", "こ", "いつ"],
    "6": ["ろ", "む", "ろく"],
    "7": ["な", "しち"],
    "8": ["は", "や", "ば", "はち"],
    "9": ["く", "き", "きゅう"],
}

HERE = os.path.dirname(os.path.abspath(__file__))
DICT_JA = os.path.join(HERE, "data", "puns.json")
DICT_ZH = os.path.join(HERE, "data", "puns-zh.json")


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


# ---------------------------------------------------------------- 日语
def combinations(digits):
    out = [""]
    for d in digits:
        opts = READINGS.get(d)
        if not opts:
            return []
        out = [a + b for a in out for b in opts]
    return out


def ja_decode(digits, show_all=False):
    combos = combinations(digits)
    d = load(DICT_JA)
    print("数字串: %s（日语）" % digits)
    print("可能的读法: %d 种" % len(combos))
    hit = d.get(digits)
    if hit:
        print("  词典命中: %s —— %s" % (digits, hit))
    elif not show_all:
        print("  词典里没有，前 30 种组合：")
        for c in combos[:30]:
            print("  " + c)
        if len(combos) > 30:
            print("  …（共 %d 种，--all 看全部）" % len(combos))
    if show_all:
        for c in combos:
            print("  " + c)


def ja_encode(text):
    table = [(r, d) for d, reads in READINGS.items() for r in reads]
    table.sort(key=lambda x: -len(x[0]))
    results = []

    def walk(s, acc, bad):
        if not s:
            results.append(("".join(acc), bad))
            return
        for r, d in table:
            if s.startswith(r):
                walk(s[len(r):], acc + [d], bad)
                return
        walk(s[1:], acc, bad + s[0])

    walk(text, [], "")
    return sorted(set(results), key=lambda x: (len(x[1]), len(x[0])))


# ---------------------------------------------------------------- 中文
def zh_load():
    d = load(DICT_ZH)
    return d.get("words", {}), d.get("chars", {})


def zh_segment(digits):
    """最长匹配切段：把数字串切成若干个"有意义的块"。
    返回 [(块, 含义), ...] 的最佳切法；切不开的位返回 None。"""
    words, chars = zh_load()
    n = len(digits)
    best = [None] * (n + 1)      # best[i] = (分数, 路径)
    best[0] = (0, [])
    for i in range(1, n + 1):
        for j in range(max(0, i - 8), i):
            if best[j] is None:
                continue
            seg = digits[j:i]
            if seg in words:
                score, path = best[j]
                cand = (score + len(seg) * 2, path + [(seg, words[seg])])   # 长词加分
                if best[i] is None or cand[0] > best[i][0]:
                    best[i] = cand
            elif len(seg) == 1 and seg in chars:
                score, path = best[j]
                cand = (score, path + [(seg, chars[seg] + "（单字）")])
                if best[i] is None or cand[0] > best[i][0]:
                    best[i] = cand
    if best[n] is None:
        return None
    return best[n][1]


def zh_decode(digits):
    print("数字串: %s（中文）" % digits)
    seg = zh_segment(digits)
    if not seg:
        print("  切不出来。词典里没有能覆盖整串的组合。")
        return
    parts = ["%s→%s" % (d, m) for d, m in seg]
    print("  切法: " + " ＋ ".join(parts))
    if len(seg) <= 4:
        print("  读作: " + "".join(m for _, m in seg).replace("（单字）", ""))


def zh_encode(phrase, words=None):
    words = words if words is not None else zh_load()[0]
    hits = [(k, v) for k, v in words.items() if v == phrase]
    if not hits:
        hits = [(k, v) for k, v in words.items() if phrase in v]
    return sorted(hits, key=lambda x: len(x[0]))


# ---------------------------------------------------------------- CLI
def main():
    ap = argparse.ArgumentParser(description="数字谐音 编码 / 解码（日语 + 中文）")
    ap.add_argument("digits", nargs="?")
    ap.add_argument("--all", action="store_true", help="日语：列出全部读法组合")
    ap.add_argument("--to", metavar="KANA", help="日语：假名 → 数字")
    ap.add_argument("--zh", action="store_true", help="中文模式：数字 → 词")
    ap.add_argument("--zh-to", metavar="词", help="中文：词 → 数字")
    a = ap.parse_args()

    if a.zh_to:
        got = zh_encode(a.zh_to)
        if not got:
            print("词典里没有「%s」对应的数字。" % a.zh_to)
            return 0
        for k, v in got[:6]:
            print("  %s → %s" % (v, k))
        return 0

    if a.zh:
        if not a.digits:
            ap.print_help()
            return 1
        zh_decode(a.digits)
        return 0

    if a.to:
        got = ja_encode(a.to)
        if not got:
            print("「%s」拆不出来" % a.to)
            return 0
        best = got[0]
        tail = "（拆不出来的字：%s）" % best[1] if best[1] else ""
        print("「%s」→ %s %s" % (a.to, best[0] or "（无）", tail))
        others = [g[0] for g in got[1:4] if not g[1]]
        if others:
            print("  也可能：%s" % "、".join(others))
        return 0

    if not a.digits:
        ap.print_help()
        return 1
    if not all(ch in READINGS for ch in a.digits):
        print("只能输入数字（0-9）", file=sys.stderr)
        return 1
    ja_decode(a.digits, a.all)
    return 0


if __name__ == "__main__":
    sys.exit(main())
