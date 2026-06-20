# -*- coding: utf-8 -*-
"""يحضّر فهرس البحث للنشر على GitHub Pages عبر sql.js-httpvfs.

- ينسخ search-index/corpus.db نسخةً مُحسَّنة بصفحات 8KB (VACUUM INTO).
- يقسّمها إلى قطع 40MB في assets/corpus/ (حدّ ملفات GitHub 100MB).
- يكتب assets/corpus/manifest.js (window.CORPUS_DB) لإعدادات httpvfs.

الاستخدام:  python scripts/build_search.py
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, setup_stdout

SRC = ROOT / "search-index" / "corpus.db"
OUT_DIR = ROOT / "assets" / "corpus"
TMP = ROOT / "search-index" / "corpus.web.db"

SERVER_CHUNK = 40 * 1024 * 1024   # 40MB لكل ملف
REQUEST_CHUNK = 8192              # غرانيلية طلبات النطاق (= حجم الصفحة)
SUFFIX_LEN = 3


def main():
    setup_stdout()
    if not SRC.exists():
        print("لا يوجد search-index/corpus.db — شغّل build_index.py أولًا.")
        sys.exit(1)

    if TMP.exists():
        TMP.unlink()
    con = sqlite3.connect(SRC)
    con.execute("PRAGMA page_size=8192")
    con.execute(f"VACUUM INTO '{TMP.as_posix()}'")
    con.close()

    # تأكيد حجم الصفحة
    c2 = sqlite3.connect(TMP)
    ps = c2.execute("PRAGMA page_size").fetchone()[0]
    c2.close()

    total = TMP.stat().st_size
    # تنظيف قطع قديمة
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.glob("corpus.sqlite3.*"):
        old.unlink()

    n = 0
    with open(TMP, "rb") as fh:
        while True:
            blk = fh.read(SERVER_CHUNK)
            if not blk:
                break
            name = f"corpus.sqlite3.{str(n).zfill(SUFFIX_LEN)}"
            (OUT_DIR / name).write_bytes(blk)
            n += 1

    manifest = (
        "window.CORPUS_DB = {\n"
        f'  urlPrefix: "assets/corpus/corpus.sqlite3.",\n'
        f"  suffixLength: {SUFFIX_LEN},\n"
        f"  serverChunkSize: {SERVER_CHUNK},\n"
        f"  requestChunkSize: {REQUEST_CHUNK},\n"
        f"  databaseLengthBytes: {total}\n"
        "};\n"
    )
    (OUT_DIR / "manifest.js").write_text(manifest, encoding="utf-8")
    TMP.unlink()
    print(
        f"✓ assets/corpus/ — {n} قطعة ({total // (1024*1024)}MB، صفحة {ps}B)، "
        f"manifest.js مكتوب"
    )


if __name__ == "__main__":
    main()
