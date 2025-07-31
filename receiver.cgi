#!/usr/bin/env python3

import sys
import os

"""
無料のレンタルサーバーに置いてるCGI
無料ゆえに貧弱なのでbot側でjinja2したHTMLを受け取って置くだけのもの
これをまた置くなら/path/to...を変える必要あり
"""

def main():
    print("Content-Type: text/plain; charset=utf-8")
    print()

    if os.environ.get("REQUEST_METHOD") != "POST":
        print("nothing received")
        return

    try:
        length = int(os.environ.get("CONTENT_LENGTH", 0))
    except (TypeError, ValueError):
        print("Invalid content length")
        return

    html = sys.stdin.read(length)
    with open("/path/to/public_html/debug.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("html received")

if __name__ == "__main__":
    main()
