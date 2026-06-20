# -*- coding: utf-8 -*-
"""يبحث في archive.org عن أمهات العلوم الحضارية (ملك عام) ويُنزّل نصّها (OCR).

- يستهدف فجوات العلوم الحضارية التراثية فقط (طب/رياضيات/فلك/فيزياء/كيمياء/
  نبات/موسيقى/صيدلة/فلسفة) — مؤلفوها قدماء فالمتن ملك عام.
- يطابق بالعنوان والمؤلف (تداخل رموز + لغة عربية)، ولا يقبل إلا تطابقًا قويًّا.
- يُنزّل <id>_djvu.txt (نص OCR) إلى corpus/_archive/<slug>.txt، ويسجّل المعرّف.
- المخرج: search-index/archive_results.json (slug -> {identifier,title,score,downloaded}).

الاستخدام:  python scripts/fetch_archive.py
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, iter_book_files, load_book, setup_stdout

OUT = ROOT / "corpus" / "_archive"
RESULTS = ROOT / "search-index" / "archive_results.json"

TARGET_SCIENCES = {
    "الفلسفة والمنطق", "الطب", "الصيدلة والأدوية المفردة", "الرياضيات",
    "الفلك وعلم الميقات", "الفيزياء والبصريات والحيل", "الكيمياء",
    "النبات والحيوان والفلاحة", "الموسيقى النظرية",
}
UA = {"User-Agent": "Mozilla/5.0 (marji-jami corpus builder)"}
STOP = {"في", "من", "على", "إلى", "عن", "كتاب", "ال", "و", "علم", "شرح", "ت"}


def norm(s):
    s = re.sub(r"[ؐ-ًؚ-ْٰۖ-ۭـ]", "", str(s or ""))
    s = s.translate(str.maketrans("أإآىة", "اااية"))
    return s


def toks(s):
    return {w for w in norm(s).split() if w not in STOP and len(w) > 2}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def search(title, author):
    core = " ".join(list(toks(title))[:4])
    q = f'({title}) AND mediatype:texts AND language:(Arabic OR ara OR arabic)'
    url = "https://archive.org/advancedsearch.php?" + urllib.parse.urlencode({
        "q": q, "rows": "8", "output": "json",
        "fl[]": "identifier",
    }, doseq=True)
    # fl[] مكرّر:
    url += "&fl[]=title&fl[]=creator&fl[]=year&fl[]=language"
    try:
        data = json.loads(get(url))
        return data.get("response", {}).get("docs", [])
    except Exception as e:
        return [{"_err": str(e)}]


def best_match(title, author, docs):
    tt = toks(title)
    at = toks(author)
    best, best_score = None, 0.0
    for d in docs:
        if "_err" in d:
            return None, 0.0, d["_err"]
        ct = toks(d.get("title", ""))
        cc = toks((d.get("creator") if isinstance(d.get("creator"), str)
                   else " ".join(d.get("creator", []))) or "")
        if not tt:
            continue
        overlap = len(tt & ct) / len(tt)
        author_bonus = 0.25 if (at & (ct | cc)) else 0
        score = overlap + author_bonus
        if score > best_score:
            best, best_score = d, score
    return best, best_score, None


def find_djvu_txt(identifier):
    meta = json.loads(get(f"https://archive.org/metadata/{identifier}"))
    files = meta.get("files", [])
    txt = [f for f in files if f.get("name", "").endswith("_djvu.txt")]
    if txt:
        return txt[0]["name"], "txt"
    pdf = sorted([f for f in files if f.get("name", "").lower().endswith(".pdf")],
                 key=lambda f: -int(f.get("size", 0) or 0))
    if pdf:
        return pdf[0]["name"], "pdf"
    return None, None


def main():
    setup_stdout()
    OUT.mkdir(parents=True, exist_ok=True)
    results = {}
    targets = []
    for ilm_dir, f in iter_book_files():
        d = load_book(f)
        if d.get("روابط_التحميل"):
            continue
        if d.get("العلم") not in TARGET_SCIENCES:
            continue
        targets.append((f.stem, d.get("العنوان", ""), (d.get("المؤلف") or {}).get("الاسم", "")))

    print(f"الأهداف: {len(targets)} كتابًا من العلوم الحضارية\n")
    for slug, title, author in targets:
        docs = search(title, author)
        cand, score, err = best_match(title, author, docs)
        rec = {"title": title, "score": round(score, 2)}
        if err:
            rec["status"] = "error:" + err
        elif cand and score >= 0.6:
            ident = cand["identifier"]
            rec["identifier"] = ident
            rec["cand_title"] = cand.get("title", "")
            try:
                fname, kind = find_djvu_txt(ident)
                if kind == "txt":
                    raw = get(f"https://archive.org/download/{ident}/{urllib.parse.quote(fname)}")
                    (OUT / (slug + ".txt")).write_bytes(raw)
                    rec["status"] = f"downloaded_txt ({len(raw)//1024}KB)"
                elif kind == "pdf":
                    rec["status"] = "pdf_only:" + fname
                else:
                    rec["status"] = "no_text_file"
            except Exception as e:
                rec["status"] = "dl_error:" + str(e)
        else:
            rec["status"] = "no_match"
            rec["best"] = (cand or {}).get("title", "") if cand else ""
        results[slug] = rec
        mark = "OK " if rec.get("status", "").startswith("downloaded") else "-- "
        print(f"{mark}{slug}  [{rec['status']}]  score={rec['score']}")
        time.sleep(1.0)

    RESULTS.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    dl = sum(1 for r in results.values() if r.get("status", "").startswith("downloaded"))
    print(f"\n✓ نُزّل نصًّا: {dl}/{len(targets)} — التفاصيل في search-index/archive_results.json")


if __name__ == "__main__":
    main()
