# -*- coding: utf-8 -*-
"""بحثٌ كاملٌ غير متّصل في نصوص كل الكتب المنزَّلة (عبر فهرس FTS5).

الاستخدام:
    python scripts/search.py الاستصحاب
    python scripts/search.py "العقل والنقل" --limit 20
    python scripts/search.py النسخ --science "أصول الفقه"

يطبّق التطبيع نفسه المستخدم في الفهرسة، ويرتّب بـ bm25، ويعرض مقتطفًا مظللًا.
"""
import argparse
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_index import DB_PATH, normalize
from common import setup_stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="+", help="كلمات البحث")
    ap.add_argument("--limit", type=int, default=15)
    ap.add_argument("--science", default="", help="حصر البحث في علم معيّن")
    args = ap.parse_args()
    setup_stdout()

    if not DB_PATH.exists():
        print("لا يوجد فهرس — شغّل build_index.py أولًا.")
        sys.exit(1)

    q = normalize(" ".join(args.query))
    # نطابق العبارة كما هي مع دعم الكلمات المتعددة
    match = " ".join(f'"{w}"' for w in q.split())

    con = sqlite3.connect(DB_PATH)
    where = "docs MATCH ?"
    where_params = [f"body : ({match})"]
    if args.science:
        where += " AND science = ?"
        where_params.append(args.science)

    rows = con.execute(
        f"SELECT title, science, book_id, "
        f"snippet(docs, 4, '«', '»', ' … ', 12) AS snip "
        f"FROM docs WHERE {where} ORDER BY bm25(docs) LIMIT ?",
        where_params + [args.limit],
    ).fetchall()

    total = con.execute(
        f"SELECT count(*) FROM docs WHERE {where}", where_params
    ).fetchone()[0]
    con.close()

    if not rows:
        print(f"لا نتائج لـ «{' '.join(args.query)}».")
        return
    print(f"نتائج «{' '.join(args.query)}» — {len(rows)} من {total} كتابًا فيه ورود:\n")
    for i, (title, science, bid, snip) in enumerate(rows, 1):
        snip = " ".join(snip.split())
        print(f"{i}. {title}  [{science}] (شاملة {bid})")
        print(f"   {snip}\n")


if __name__ == "__main__":
    main()
