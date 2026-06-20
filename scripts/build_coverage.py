# -*- coding: utf-8 -*-
"""تقرير التغطية: حالة كل كتاب من حيث توفّر النص الكامل.

التصنيفات:
  ✅ محمَّل        — نصّه الكامل موجود في corpus/ (مفهرس للبحث)
  📥 حر غير محمَّل — له رابط حر لكن لا نصّ محلي (مصدر غير الشاملة أو لم يُنزَّل)
  🛒 شراء فقط      — لا مصدر حر، رابط شراء فقط
  ❓ بلا رابط      — لا رابط بعد ← فجوة: يحتاج PDF أو بحثًا

يكتب docs/التغطية.md ويطبع ملخّصًا + قائمة الفجوات.

الاستخدام:  python scripts/build_coverage.py
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, ULUM, iter_book_files, load_book, setup_stdout

CORPUS = ROOT / "corpus"
DOCS = ROOT / "docs"


def corpus_ids():
    if not CORPUS.exists():
        return set()
    return {p.stem for p in CORPUS.rglob("*.txt")}


def shamela_id(url):
    m = re.search(r"shamela\.ws/book/(\d+)", str(url or ""))
    return m.group(1) if m else None


def main():
    setup_stdout()
    have = corpus_ids()
    order = {n: i for i, n in enumerate(ULUM)}
    rows = []
    for ilm_dir, f in iter_book_files():
        d = load_book(f)
        links = d.get("روابط_التحميل") or []
        free = [l for l in links if isinstance(l, dict) and l.get("النوع") == "حر"]
        buy = [l for l in links if isinstance(l, dict) and l.get("النوع") == "شراء"]
        sid = next((shamela_id(l.get("الرابط")) for l in free if shamela_id(l.get("الرابط"))), None)
        downloaded = bool(sid and sid in have)
        avail = str((d.get("التوافر_الرقمي") or {}).get("المكتبة_الشاملة", "")).strip()
        if downloaded:
            status, rank = "✅ محمَّل", 0
        elif free:
            status, rank = "📥 حر غير محمَّل (متاح أونلاين)", 1
        elif avail == "نعم":
            status, rank = "🔎 على الشاملة — سأنزّلها", 2
        elif buy:
            status, rank = "🛒 شراء فقط — يحتاج PDF منك", 3
        else:
            status, rank = "❓ يحتاج PDF منك (لا مصدر حر)", 4
        rows.append({
            "slug": d.get("id", f.stem),
            "title": d.get("العنوان", f.stem),
            "science": d.get("العلم", ilm_dir.name),
            "sid": sid or "",
            "shamela_avail": (d.get("التوافر_الرقمي") or {}).get("المكتبة_الشاملة", ""),
            "status": status, "rank": rank,
            "sci_order": order.get(d.get("العلم", ""), 999),
        })

    counts = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    total = len(rows)

    # تقرير ماركداون
    DOCS.mkdir(exist_ok=True)
    STATES = [
        "✅ محمَّل", "📥 حر غير محمَّل (متاح أونلاين)",
        "🔎 على الشاملة — سأنزّلها", "🛒 شراء فقط — يحتاج PDF منك",
        "❓ يحتاج PDF منك (لا مصدر حر)",
    ]
    lines = ["# تقرير التغطية — توفّر النصوص الكاملة", ""]
    lines.append(f"المجموع: **{total}** كتابًا.")
    for st in STATES:
        lines.append(f"- {st}: **{counts.get(st, 0)}**")
    lines.append("")
    lines.append("## ما يحتاج PDF منك (الفجوات الحقيقية) — مرتّبة بالعلم")
    lines.append("> هذه الكتب لا مصدر حرّ لها؛ زوّدني بـPDF لكلٍّ منها (بالاسم المختصر `[slug]`).")
    lines.append("")
    gaps = [r for r in rows if r["rank"] >= 3]
    gaps.sort(key=lambda r: (r["sci_order"], r["title"]))
    cur = None
    for r in gaps:
        if r["science"] != cur:
            cur = r["science"]
            lines.append(f"\n### {cur}")
        note = "(الشاملة: " + str(r["shamela_avail"]) + ")" if r["shamela_avail"] else ""
        lines.append(f"- {r['status']} — **{r['title']}** `[{r['slug']}]` {note}")
    (DOCS / "التغطية.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ملخّص للطرفية
    print(f"إجمالي الكتب: {total}")
    for st in STATES:
        print(f"  {st}: {counts.get(st, 0)}")
    print(f"\n✓ docs/التغطية.md — يحتاج PDF منك: {len(gaps)} كتابًا")


if __name__ == "__main__":
    main()
