# -*- coding: utf-8 -*-
"""يولّد بيانات موقع GitHub Pages (assets/data.js) من ملفات data/.

الموقع تطبيق صفحة واحدة (SPA) عربي RTL متجاوب مع الجوال:
index.html + assets/style.css + assets/app.js (مكتوبة يدويًّا) + assets/data.js (هذا المولّد).

يُخرَج data.js كمتغيّر عام window.MARJI ليعمل على file:// وعلى Pages بلا fetch.

الاستخدام:  python scripts/build_site.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, ULUM, iter_book_files, load_book, setup_stdout

ASSETS = ROOT / "assets"

PILLAR_1 = "التراث الشرعي واللغوي والأدبي"
PILLAR_2 = "العلوم الحضارية التراثية"
PILLAR_3 = "المراجع المعاصرة بالعربية"


def pillar_of(idx):
    if idx <= 20:
        return PILLAR_1
    if 22 <= idx <= 32:
        return PILLAR_2
    return PILLAR_3  # idx == 21 (المراجع المكملة) أو 33..38 (المعاصرة)


def fmt_author(m):
    if not isinstance(m, dict):
        return str(m or "")
    name = m.get("الاسم", "")
    wh = m.get("الوفاة_هجري")
    wm = m.get("الوفاة_ميلادي")
    if wh:
        d = f"ت {wh}هـ" + (f"/{wm}م" if wm else "")
        return f"{name} ({d})"
    if wm:
        return f"{name} (ت {wm}م)"
    return name


def short_editions(eds):
    out = []
    for e in eds or []:
        if not isinstance(e, dict):
            continue
        out.append(
            {
                "ed": e.get("المحقق_أو_المعتني", ""),
                "dar": e.get("الدار", ""),
                "year": e.get("السنة", ""),
                "vols": e.get("المجلدات", ""),
                "note": e.get("ملاحظة", ""),
            }
        )
    return out


def aslist(v):
    if not v:
        return []
    if isinstance(v, list):
        return [str(x) for x in v]
    return [str(v)]


def main():
    setup_stdout()
    ASSETS.mkdir(exist_ok=True)
    order = {name: i for i, name in enumerate(ULUM)}

    books = []
    sci_count = {}
    for ilm_dir, f in iter_book_files():
        d = load_book(f)
        ilm = d.get("العلم", "")
        idx = order.get(ilm, 999)
        links = []
        for ln in d.get("روابط_التحميل") or []:
            if isinstance(ln, dict):
                links.append(
                    {
                        "src": ln.get("المصدر", ""),
                        "url": ln.get("الرابط", ""),
                        "type": ln.get("النوع", ""),
                    }
                )
        books.append(
            {
                "id": d.get("id", f.stem),
                "science": ilm,
                "pillar": pillar_of(idx),
                "title": d.get("العنوان", ""),
                "author": fmt_author(d.get("المؤلف")),
                "sub": d.get("التصنيف_الفرعي", ""),
                "why": (d.get("لماذا_هو_أم_في_بابه") or "").strip(),
                "replaces": aslist(d.get("يغني_عن")),
                "before": aslist(d.get("يُقرأ_قبله")),
                "editions": short_editions(d.get("أفضل_الطبعات")),
                "commentaries": aslist(d.get("الشروح_والمختصرات_والذيول")),
                "level": d.get("مستوى_القارئ", ""),
                "type": d.get("نوع_المرجعية", ""),
                "critique": (d.get("ملاحظات_نقدية") or "").strip(),
                "links": links,
                "translated": bool(d.get("مترجَم")),
                "translator": d.get("المترجِم", ""),
                "translationBody": d.get("جهة_الترجمة", ""),
                "modern": bool(d.get("معاصر")),
            }
        )
        sci_count[ilm] = sci_count.get(ilm, 0) + 1

    books.sort(key=lambda b: (order.get(b["science"], 999), b["title"]))
    sciences = [
        {"name": n, "pillar": pillar_of(i), "count": sci_count.get(n, 0)}
        for i, n in enumerate(ULUM)
        if sci_count.get(n)
    ]
    free = sum(1 for b in books if any(l["type"] == "حر" for l in b["links"]))

    payload = {
        "pillars": [PILLAR_1, PILLAR_2, PILLAR_3],
        "sciences": sciences,
        "books": books,
        "stats": {
            "books": len(books),
            "sciences": len(sciences),
            "free": free,
        },
    }
    data_js = "window.MARJI = " + json.dumps(payload, ensure_ascii=False) + ";\n"
    (ASSETS / "data.js").write_text(data_js, encoding="utf-8")
    size_kb = (ASSETS / "data.js").stat().st_size // 1024
    print(
        f"✓ assets/data.js — {len(books)} كتابًا في {len(sciences)} علمًا، "
        f"{free} رابطًا حرًّا ({size_kb}KB)"
    )


if __name__ == "__main__":
    main()
