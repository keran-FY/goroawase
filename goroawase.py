#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""goroawase —— 数字谐音（語呂合わせ）的编码与解码。

日语里有一整套"把数字读成假名、再拼成词"的玩法：
    0 → お / れ / ぜ       1 → い / ひ        2 → に / ふ / じ
    3 → さ / み            4 → し / よ       5 → ご / こ
    6 → ろ / む            7 → な            8 → は / や / ば
    9 → く / き

所以 0721 → お な に い → オナニー。
这是网上流传最广的一条，但根本不是唯一的一条——同一个数字串
可以对应几千种读法，靠一本小词典把"读得通"的挑出来。

用法：
    python goroawase.py 0721          # 解：这个数字串能读成什么
    python goroawase.py 4649 --all    # 列出全部组合（不加 --all 只挑词典里的）
    python goroawase.py --to ありがとう   # 反查：这个词对应哪个数字
"""
import argparse
import json
import os
import sys

# 数字 → 可以读成哪些假名（常用读法，不求穷尽）
READINGS = {
    "0": ["お", "れ", "ぜ", "わ", "まる"],
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
DICT = os.path.join(HERE, "data", "puns.json")


def load_dict():
    try:
        with open(DICT, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def combinations(digits, limit=None):
    """把数字串拆成所有可能的假名组合（按位置逐个替换）。"""
    out = [""]
    for d in digits:
        opts = READINGS.get(d)
        if not opts:
            return []
        out = [a + b for a in out for b in opts]
        if limit and len(out) > limit:
            out = out[:limit]
    return out


def decode(digits, show_all=False):
    combos = combinations(digits)
    d = load_dict()
    known = [(k, v) for k, v in d.items() if k in digits or v in combos]
    hits = [(v, d.get(v)) for v in combos if v in d]
    known = d.get(digits)

    print("数字串: %s" % digits)
    print("可能的读法: %d 种" % len(combos))
    if known:
        print("  词典命中: %s —— %s" % (digits, known))
    if hits:
        for kana, note in hits:
            print("  读成「%s」%s" % (kana, (" —— " + note) if note else ""))
    if show_all:
        print("\n全部组合：")
        for c in combos:
            print("  " + c)
    elif not known and not hits:
        print("  词典里没有，试 --all 看全部组合：")
        for c in combos[:30]:
            print("  " + c)
        if len(combos) > 30:
            print("  …（共 %d 种）" % len(combos))


def encode(text):
    """反查：把假名词拆成数字，返回 (所有可能, 拆不出来的字)。贪心，最长匹配优先。"""
    table = []
    for d, reads in READINGS.items():
        for r in reads:
            table.append((r, d))
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
        # 这个字拆不出来，跳过它继续
        walk(s[1:], acc, bad + s[0])

    walk(text, [], "")
    return sorted(set(results), key=lambda x: (len(x[1]), len(x[0])))


def main():
    ap = argparse.ArgumentParser(description="数字谐音 编码 / 解码")
    ap.add_argument("digits", nargs="?", help="数字串，如 0721")
    ap.add_argument("--all", action="store_true", help="列出全部读法组合")
    ap.add_argument("--to", metavar="KANA", help="反查：假名 → 数字")
    a = ap.parse_args()

    if a.to:
        got = encode(a.to)
        if not got:
            print("「%s」拆不出来" % a.to)
            return 0
        best = got[0]
        if best[1]:
            print("「%s」→ %s （拆不出来的字：%s）" % (a.to, best[0] or "（无）", best[1]))
        else:
            print("「%s」→ %s" % (a.to, best[0]))
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
    decode(a.digits, a.all)
    return 0


if __name__ == "__main__":
    sys.exit(main())
