# -*- coding: utf-8 -*-
"""يبني فهرس بحثٍ كامل (SQLite FTS5) فوق نصوص corpus/ المستخرَجة.

- يطابق كل ملف نصٍّ بالكتاب المقابل في data/ ليأخذ العنوان والعلم والمؤلف.
- يطبّق تطبيعًا عربيًّا (إزالة التشكيل والتطويل، توحيد الألف والياء والتاء المربوطة)
  على نص الفهرسة لرفع دقة الاسترجاع، ويطبّق نفسه على الاستعلام في search.py.
- المخرج: search-index/corpus.db (مستثنى من git).

الاستخدام:  python scripts/build_index.py
"""
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, iter_book_files, load_book, setup_stdout

CORPUS = ROOT / "corpus"
INDEX_DIR = ROOT / "search-index"
DB_PATH = INDEX_DIR / "corpus.db"

_TASHKEEL = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭـ]")


def normalize(text):
    text = _TASHKEEL.sub("", text)
    text = text.translate(str.maketrans("أإآىة", "اااية"))
    return text


def meta_maps():
    """يربط بيانات الكتاب بمفتاحين: رقم الشاملة (للمنزَّل) والمعرّف المختصر (لملفات PDF)."""
    out = {}
    for ilm_dir, f in iter_book_files():
        data = load_book(f)
        info = {
            "science": data.get("العلم", ilm_dir.name),
            "title": data.get("العنوان", f.stem),
            "author": (data.get("المؤلف") or {}).get("الاسم", ""),
            "slug": f.stem,
        }
        out[f.stem] = info            # المفتاح بالمعرّف المختصر (لملفات PDF المُدخَلة)
        if data.get("id"):
            out[data["id"]] = info
        for link in data.get("روابط_التحميل") or []:
            if isinstance(link, dict) and link.get("النوع") == "حر":
                m = re.search(r"shamela\.ws/book/(\d+)", str(link.get("الرابط", "")))
                if m:
                    out[m.group(1)] = info   # المفتاح برقم الشاملة (للمنزَّل)
    return out


def main():
    setup_stdout()
    if not CORPUS.exists():
        print("لا يوجد مجلد corpus/ بعد — شغّل fetch_texts.py أولًا.")
        sys.exit(1)
    INDEX_DIR.mkdir(exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    meta = meta_maps()
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "CREATE VIRTUAL TABLE docs USING fts5("
        "book_id UNINDEXED, science UNINDEXED, title, author, body, "
        "tokenize='unicode61 remove_diacritics 2')"
    )

    count = words = 0
    for txt in sorted(CORPUS.rglob("*.txt")):
        bid = txt.stem
        info = meta.get(bid, {})
        body = txt.read_text(encoding="utf-8")
        words += len(body.split())
        con.execute(
            "INSERT INTO docs(book_id, science, title, author, body) "
            "VALUES (?,?,?,?,?)",
            (
                bid,
                info.get("science", ""),
                normalize(info.get("title", bid)),
                normalize(info.get("author", "")),
                normalize(body),
            ),
        )
        count += 1
    con.commit()
    con.execute("INSERT INTO docs(docs) VALUES('optimize')")
    con.commit()
    con.close()
    size_mb = DB_PATH.stat().st_size // (1024 * 1024)
    print(f"✓ فُهرس {count} كتابًا، {words:,} كلمة — {DB_PATH} ({size_mb}MB)")


if __name__ == "__main__":
    main()
