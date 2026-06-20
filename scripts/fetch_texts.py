# -*- coding: utf-8 -*-
"""تنزيل النص الكامل للكتب التي لها رابط حر على المكتبة الشاملة، واستخراج نصّها.

- يقرأ كل ملفات data/، ويستخرج رقم كتاب الشاملة من حقل «روابط_التحميل».
- ينزّل ملف EPUB من الشاملة (نمط: old.shamela.ws/epubs/<floor(id/100)>/<id>.epub).
- يستخرج النص النظيف من الـEPUB (بترتيب الـspine) إلى ملف .txt.
- المخرجات في corpus/<مجلد العلم>/<id>.epub و<id>.txt — كلها مستثناة من git.

الاستخدام:
    python scripts/fetch_texts.py            # كل الكتب التي لها رابط شاملة حر
    python scripts/fetch_texts.py --limit 5  # أول 5 فقط (للاختبار)
    python scripts/fetch_texts.py --redo     # يعيد التنزيل ولو كان موجودًا

ملاحظة قانونية: تحقيقات الشاملة محمية؛ هذه نسخٌ للاستعمال الشخصي المحلي فقط،
ولا تُرفع إلى المستودع (مجلد corpus/ مستثنى في .gitignore).
"""
import argparse
import re
import sys
import time
import urllib.request
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, iter_book_files, load_book, setup_stdout

CORPUS = ROOT / "corpus"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) marji-jami/1.0"
SHAMELA_ID_RE = re.compile(r"shamela\.ws/book/(\d+)")


def shamela_id_of(data):
    """يعيد رقم كتاب الشاملة من أول رابط حر، أو None."""
    for link in data.get("روابط_التحميل") or []:
        if not isinstance(link, dict):
            continue
        if link.get("النوع") != "حر":
            continue
        m = SHAMELA_ID_RE.search(str(link.get("الرابط", "")))
        if m:
            return m.group(1)
    return None


def epub_url(book_id):
    folder = f"{int(book_id) // 100:03d}"
    return f"https://old.shamela.ws/epubs/{folder}/{book_id}.epub"


def download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()
    dest.write_bytes(data)
    return len(data)


class _TextStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip += 1
        if tag in ("p", "div", "br", "h1", "h2", "h3", "li"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)


def _strip_html(html_bytes):
    try:
        html = html_bytes.decode("utf-8")
    except UnicodeDecodeError:
        html = html_bytes.decode("utf-8", "replace")
    p = _TextStripper()
    p.feed(html)
    return "".join(p.parts)


def _spine_order(zf):
    """يعيد قائمة مسارات xhtml بترتيب الـspine إن أمكن، وإلا كل ملفات النص مرتّبة."""
    opf_name = None
    for n in zf.namelist():
        if n.endswith(".opf"):
            opf_name = n
            break
    names = zf.namelist()
    if not opf_name:
        return sorted(n for n in names if n.endswith((".xhtml", ".html", ".htm")))
    try:
        root = ET.fromstring(zf.read(opf_name))
    except ET.ParseError:
        return sorted(n for n in names if n.endswith((".xhtml", ".html", ".htm")))

    def local(tag):
        return tag.rsplit("}", 1)[-1]

    base = opf_name.rsplit("/", 1)[0] if "/" in opf_name else ""
    manifest, spine = {}, []
    for el in root.iter():
        if local(el.tag) == "item":
            manifest[el.get("id")] = el.get("href")
        elif local(el.tag) == "itemref":
            spine.append(el.get("idref"))
    ordered = []
    for idref in spine:
        href = manifest.get(idref)
        if not href:
            continue
        path = f"{base}/{href}" if base else href
        path = path.replace("\\", "/")
        if path in zf.namelist():
            ordered.append(path)
    return ordered or sorted(
        n for n in names if n.endswith((".xhtml", ".html", ".htm"))
    )


def extract_text(epub_path):
    out = []
    with zipfile.ZipFile(epub_path) as zf:
        for name in _spine_order(zf):
            txt = _strip_html(zf.read(name))
            txt = re.sub(r"\n{3,}", "\n\n", txt)
            txt = re.sub(r"[ \t]+", " ", txt)
            out.append(txt.strip())
    return "\n\n".join(t for t in out if t)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--redo", action="store_true")
    args = ap.parse_args()
    setup_stdout()

    jobs = []
    for ilm_dir, f in iter_book_files():
        data = load_book(f)
        bid = shamela_id_of(data)
        if bid:
            jobs.append((ilm_dir.name, f.stem, bid))
    if args.limit:
        jobs = jobs[: args.limit]

    print(f"كتب لها رقم شاملة حر: {len(jobs)}")
    ok = skipped = failed = 0
    total_bytes = 0
    for i, (ilm, slug, bid) in enumerate(jobs, 1):
        outdir = CORPUS / ilm
        outdir.mkdir(parents=True, exist_ok=True)
        epub_path = outdir / f"{bid}.epub"
        txt_path = outdir / f"{bid}.txt"
        if txt_path.exists() and not args.redo:
            skipped += 1
            continue
        url = epub_url(bid)
        try:
            if not epub_path.exists() or args.redo:
                n = download(url, epub_path)
                total_bytes += n
                time.sleep(0.5)
            text = extract_text(epub_path)
            txt_path.write_text(text, encoding="utf-8")
            kb = epub_path.stat().st_size // 1024
            words = len(text.split())
            print(f"[{i}/{len(jobs)}] ✓ {slug} (id {bid}) — {kb}KB، {words} كلمة")
            ok += 1
        except Exception as e:
            print(f"[{i}/{len(jobs)}] ✗ {slug} (id {bid}) — {e}")
            failed += 1
    print(
        f"\nتم: {ok} نُزّلت، {skipped} موجودة، {failed} فشلت. "
        f"المنزَّل: {total_bytes // (1024*1024)}MB"
    )


if __name__ == "__main__":
    main()
