# -*- coding: utf-8 -*-
"""يُدخِل ملفات PDF التي يزوّدها المستخدم إلى مدوّنة البحث.

- ضع ملفات PDF في incoming-pdfs/ باسم المعرّف المختصر للكتاب: <slug>.pdf
  (المعرّفات في docs/التغطية.md، مثل tafsir-al-tabari.pdf).
- يستخرج النص بـpypdf ويحفظه في corpus/_pdf/<slug>.txt ليلتقطه build_index.py.
- يُبلِّغ عن غير المطابِق (اسم لا يقابل كتابًا) ليصحّحه المستخدم.

بعده: build_index.py ← build_search.py ← رفع القطع الجديدة.

الاستخدام:  python scripts/ingest_pdfs.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, iter_book_files, load_book, setup_stdout

INCOMING = ROOT / "incoming-pdfs"
OUT = ROOT / "corpus" / "_pdf"


def valid_slugs():
    s = set()
    for _, f in iter_book_files():
        s.add(f.stem)
        d = load_book(f)
        if d.get("id"):
            s.add(d["id"])
    return s


def main():
    setup_stdout()
    from pypdf import PdfReader  # تأخير الاستيراد لرسالة خطأ أوضح
    if not INCOMING.exists():
        INCOMING.mkdir(parents=True)
        print(f"أُنشئ {INCOMING} — ضع فيه ملفات <slug>.pdf ثم أعد التشغيل.")
        return
    OUT.mkdir(parents=True, exist_ok=True)
    slugs = valid_slugs()
    matched, unmatched, failed = [], [], []
    for pdf in sorted(INCOMING.glob("*.pdf")):
        slug = pdf.stem
        if slug not in slugs:
            unmatched.append(slug)
            continue
        try:
            reader = PdfReader(str(pdf))
            text = "\n".join((p.extract_text() or "") for p in reader.pages)
            if len(text.strip()) < 200:
                failed.append(slug + " (نص ضئيل — قد يكون PDF صورة يحتاج OCR)")
                continue
            (OUT / (slug + ".txt")).write_text(text, encoding="utf-8")
            matched.append(slug)
        except Exception as e:
            failed.append(f"{slug} ({e})")

    print(f"أُدخِل: {len(matched)} كتابًا")
    for s in matched:
        print("  ✅", s)
    if unmatched:
        print(f"\nاسم لا يقابل كتابًا ({len(unmatched)}) — صحّح التسمية للـslug الصحيح:")
        for s in unmatched:
            print("  ❓", s)
    if failed:
        print(f"\nتعذّر الاستخراج ({len(failed)}):")
        for s in failed:
            print("  ✗", s)
    if matched:
        print("\nالتالي: python scripts/build_index.py ثم build_search.py ثم رفع القطع.")


if __name__ == "__main__":
    main()
