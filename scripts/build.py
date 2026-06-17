# -*- coding: utf-8 -*-
"""توليد docs/ من data/. لا تُحرَّر مخرجات docs/ يدويًا.

الاستخدام:  python scripts/build.py   (شغّل validate.py أولًا)
"""
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (DATA, DOCS, ULUM, ilm_dirname, load_all_books,
                    setup_stdout, strip_shadda)

TANBIH = "<!-- ملف مولّد آليًا بـ scripts/build.py — لا تحرره يدويًا -->\n\n"

QURUN = ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس", "السابع",
         "الثامن", "التاسع", "العاشر", "الحادي عشر", "الثاني عشر",
         "الثالث عشر", "الرابع عشر", "الخامس عشر"]


def fmt_author(b):
    m = b.get("المؤلف", {}) or {}
    name = m.get("الاسم", "؟")
    wh, wm = m.get("الوفاة_هجري"), m.get("الوفاة_ميلادي")
    if isinstance(wh, int):
        s = f"{name} (ت {wh}هـ"
        if isinstance(wm, int):
            s += f" / {wm}م"
        return s + ")"
    if m.get("هيئة") in ("نعم", True):
        return f"{name} (هيئة)"
    if isinstance(wm, int):  # مؤلف أجنبي مترجَم بالتاريخ الميلادي وحده
        return f"{name} (ت {wm}م)"
    return f"{name} (معاصر)"


def fmt_list(v):
    if not v:
        return None
    if isinstance(v, list):
        return "؛ ".join(str(x) for x in v)
    return str(v)


def book_card(b):
    lines = [f"### {b['العنوان']}", ""]
    lines.append(f"**المؤلف:** {fmt_author(b)}  ")
    if b.get("التصنيف_الفرعي"):
        lines.append(f"**التصنيف الفرعي:** {b['التصنيف_الفرعي']}  ")
    naw = b.get("نوع_المرجعية", "؟")
    if b.get("مترجَم") in ("نعم", True):
        naw += " — مترجَم 📖"
    lines.append(f"**مستوى القارئ:** {b.get('مستوى_القارئ', '؟')} · "
                 f"**نوع المرجعية:** {naw} · "
                 f"**حالة التوثيق:** {b.get('حالة_التوثيق', '؟')}")
    lines.append("")
    if b.get("مترجَم") in ("نعم", True):
        tparts = []
        if b.get("المترجِم"):
            tparts.append(f"ترجمة: {b['المترجِم']}")
        if b.get("جهة_الترجمة"):
            tparts.append(str(b["جهة_الترجمة"]))
        if tparts:
            lines.append(f"**الترجمة:** {'، '.join(tparts)}.")
            lines.append("")
    lines.append(f"**لماذا هو أمٌّ في بابه:** {str(b.get('لماذا_هو_أم_في_بابه', '')).strip()}")
    lines.append("")
    for key, label in [("يغني_عن", "يغني عن"), ("يُقرأ_قبله", "يُقرأ قبله")]:
        v = fmt_list(b.get(key))
        if v:
            lines.append(f"**{label}:** {v}.")
            lines.append("")
    tab = b.get("أفضل_الطبعات") or []
    if tab:
        lines.append("**أفضل الطبعات:**")
        lines.append("")
        for t in tab:
            parts = []
            if t.get("المحقق_أو_المعتني"):
                parts.append(f"تحقيق/عناية: {t['المحقق_أو_المعتني']}")
            if t.get("الدار"):
                parts.append(str(t["الدار"]))
            if t.get("السنة"):
                parts.append(f"سنة {t['السنة']}")
            if t.get("المجلدات"):
                parts.append(f"{t['المجلدات']} مجلدًا" if str(t['المجلدات']).isdigit() else str(t['المجلدات']))
            line = f"- {'، '.join(parts)}"
            if t.get("ملاحظة"):
                line += f" — {t['ملاحظة']}"
            lines.append(line)
        lines.append("")
    taw = b.get("التوافر_الرقمي") or {}
    if taw:
        parts = []
        if "المكتبة_الشاملة" in taw:
            parts.append(f"المكتبة الشاملة: {taw['المكتبة_الشاملة']}")
        other = fmt_list(taw.get("منصات_أخرى"))
        if other:
            parts.append(f"منصات أخرى: {other}")
        if parts:
            lines.append(f"**التوافر الرقمي:** {'؛ '.join(parts)}.")
            lines.append("")
    v = fmt_list(b.get("الشروح_والمختصرات_والذيول"))
    if v:
        lines.append(f"**الشروح والمختصرات والذيول:** {v}.")
        lines.append("")
    rd = b.get("روابط_التحميل") or []
    if rd:
        items = []
        for r in rd:
            tag = "حر" if str(r.get("النوع", "")).strip() == "حر" else "شراء"
            emoji = "📥" if tag == "حر" else "🛒"
            items.append(f"{emoji} [{r.get('المصدر', 'رابط')}]({r.get('الرابط', '')}) ({tag})")
        lines.append(f"**روابط التحميل:** {' · '.join(items)}")
        lines.append("")
    if b.get("ملاحظات_نقدية"):
        lines.append(f"**ملاحظات نقدية:** {str(b['ملاحظات_نقدية']).strip()}")
        lines.append("")
    masadir = fmt_list(b.get("مصادر_التوثيق"))
    foot = []
    if masadir:
        foot.append(f"مصادر التوثيق: {masadir}")
    if b.get("آخر_تحديث"):
        foot.append(f"آخر تحديث: {b['آخر_تحديث']}")
    if foot:
        lines.append(f"<sub>{' · '.join(foot)}</sub>")
        lines.append("")
    return "\n".join(lines)


def ilm_page(ilm, books):
    out = [TANBIH + f"# {ilm}", ""]
    intro_file = DATA / ilm_dirname(ilm) / "_تمهيد.md"
    if intro_file.exists():
        out.append(intro_file.read_text(encoding="utf-8").strip())
    else:
        out.append("> ⚠ تمهيد هذا العلم لم يُكتب بعد (`data/" + ilm_dirname(ilm) + "/_تمهيد.md`).")
    out.append("")
    out.append("## جدول موجز")
    out.append("")
    out.append("| الكتاب | المؤلف | التصنيف الفرعي | المستوى | التوثيق |")
    out.append("|---|---|---|---|---|")
    for b in books:
        out.append(f"| [{b['العنوان']}](#{anchor(b['العنوان'])}) | {fmt_author(b)} | "
                   f"{b.get('التصنيف_الفرعي', '—') or '—'} | {b.get('مستوى_القارئ', '؟')} | "
                   f"{b.get('حالة_التوثيق', '؟')} |")
    out.append("")
    out.append("## بطاقات الكتب")
    out.append("")
    for b in books:
        out.append(book_card(b))
        out.append("---")
        out.append("")
    return "\n".join(out)


def anchor(title):
    return str(title).replace(" ", "-")


def sort_key(b):
    m = b.get("المؤلف", {}) or {}
    return (m.get("الوفاة_هجري") or 9999, b.get("العنوان", ""))


def main():
    setup_stdout()
    DOCS.mkdir(exist_ok=True)
    all_books = [b for _, _, b in load_all_books()]
    by_ilm = {}
    for b in all_books:
        by_ilm.setdefault(b.get("العلم"), []).append(b)
    for books in by_ilm.values():
        books.sort(key=sort_key)

    # صفحات العلوم
    pages = 0
    for ilm in ULUM:
        if ilm in by_ilm:
            (DOCS / f"{ilm_dirname(ilm)}.md").write_text(
                ilm_page(ilm, by_ilm[ilm]), encoding="utf-8")
            pages += 1

    # الفهرس العام
    idx = [TANBIH + "# المرجع الجامع لأمهات الكتب الإسلامية والعربية", ""]
    idx.append("الفهرس العام — انظر [المنهج](../MANHAJ.md) لمعايير الإدخال.")
    idx.append("")
    idx.append("| # | العلم | عدد الكتب |")
    idx.append("|---|---|---|")
    for i, ilm in enumerate(ULUM, 1):
        n = len(by_ilm.get(ilm, []))
        cell = f"[{ilm}]({ilm_dirname(ilm)}.md)" if n else f"{ilm} *(لم يُغطَّ بعد)*"
        idx.append(f"| {i} | {cell} | {n} |")
    idx.append("")
    idx.append(f"**المجموع: {len(all_books)} كتابًا في {pages} علمًا.**")
    idx.append("")
    kharita = DATA / "_خارطة-طالب-العلم.md"
    if kharita.exists():
        idx.append(kharita.read_text(encoding="utf-8").strip())
        idx.append("")
    idx.append("فهارس مساعدة: [المؤلفون](فهرس-المؤلفين.md) · [القرون](فهرس-القرون.md) · [الإحصاءات](إحصاءات.md) · [روابط التحميل](روابط-التحميل.md)")
    (DOCS / "index.md").write_text("\n".join(idx), encoding="utf-8")

    # فهرس المؤلفين
    by_author = {}
    for b in all_books:
        by_author.setdefault(fmt_author(b), []).append(b)
    fa = [TANBIH + "# فهرس المؤلفين", ""]
    for author in sorted(by_author):
        fa.append(f"- **{author}**")
        for b in sorted(by_author[author], key=lambda x: x.get("العنوان", "")):
            fa.append(f"  - {b['العنوان']} — [{b['العلم']}]({ilm_dirname(b['العلم'])}.md)")
    (DOCS / "فهرس-المؤلفين.md").write_text("\n".join(fa) + "\n", encoding="utf-8")

    # فهرس القرون
    by_qarn = {}
    for b in all_books:
        wh = (b.get("المؤلف") or {}).get("الوفاة_هجري")
        q = (wh - 1) // 100 + 1 if isinstance(wh, int) else None
        by_qarn.setdefault(q, []).append(b)
    fq = [TANBIH + "# فهرس القرون (بوفاة المؤلف هجريًا)", ""]
    for q in sorted([k for k in by_qarn if k], key=int):
        name = QURUN[q - 1] if q <= len(QURUN) else str(q)
        fq.append(f"## القرن {name} الهجري")
        fq.append("")
        for b in sorted(by_qarn[q], key=sort_key):
            fq.append(f"- {b['العنوان']} — {fmt_author(b)} — {b['العلم']}")
        fq.append("")
    if None in by_qarn:
        fq.append("## معاصرون وهيئات")
        fq.append("")
        for b in sorted(by_qarn[None], key=lambda x: x.get("العنوان", "")):
            fq.append(f"- {b['العنوان']} — {fmt_author(b)} — {b['العلم']}")
        fq.append("")
    (DOCS / "فهرس-القرون.md").write_text("\n".join(fq), encoding="utf-8")

    # الإحصاءات
    st = [TANBIH + "# إحصاءات", ""]
    st.append(f"- مجموع الكتب: **{len(all_books)}**")
    st.append(f"- العلوم المغطاة: **{pages} / {len(ULUM)}**")
    for nau in ["شرعية_لغوية", "علمية_تراثية_حضارية", "معاصرة"]:
        n = sum(1 for b in all_books if b.get("نوع_المرجعية") == nau)
        st.append(f"- نوع المرجعية {nau}: {n}")
    needs = [b for b in all_books if strip_shadda(b.get("حالة_التوثيق", "")) == "يحتاج_تحقق"]
    pct = 100 * len(needs) / len(all_books) if all_books else 0
    flag = " ⚠ **تجاوزت حد 15%**" if pct > 15 else ""
    st.append(f"- الموسومة «يحتاج_تحقق»: {len(needs)} ({pct:.1f}%){flag}")
    st.append("")
    st.append("## عدد الكتب في كل علم")
    st.append("")
    st.append("| العلم | العدد |")
    st.append("|---|---|")
    for ilm in ULUM:
        if ilm in by_ilm:
            st.append(f"| {ilm} | {len(by_ilm[ilm])} |")
    st.append("")
    st.append("## قائمة الكتب التي تحتاج تحققًا")
    st.append("")
    if needs:
        for b in sorted(needs, key=lambda x: (x.get("العلم", ""), x.get("العنوان", ""))):
            st.append(f"- {b['العنوان']} ({b['العلم']}) — id: `{b['id']}`")
    else:
        st.append("لا شيء — كل الكتب موثقة. ✓")
    st.append("")
    st.append(f"<sub>وُلّد في {datetime.date.today()}</sub>")
    (DOCS / "إحصاءات.md").write_text("\n".join(st) + "\n", encoding="utf-8")

    # فهرس روابط التحميل
    dl = [TANBIH + "# روابط التحميل", ""]
    dl.append("مصادر تحميل ملفات الكتب، مميَّزةً: 📥 **حر** (ملك عام أو متاح مجانًا من جهته) · "
              "🛒 **شراء** (محمي بحقوق النشر، يُقتنى قانونيًّا). "
              "تُحفظ الملفات المحمَّلة في مجلد `pdfs/<العلم>/` (مستثنى من git).")
    dl.append("")
    has_free = sum(1 for b in all_books
                   if any(str(r.get("النوع", "")).strip() == "حر" for r in (b.get("روابط_التحميل") or [])))
    has_buy = sum(1 for b in all_books
                  if (b.get("روابط_التحميل") or []) and not any(
                      str(r.get("النوع", "")).strip() == "حر" for r in b.get("روابط_التحميل")))
    none_n = sum(1 for b in all_books if not (b.get("روابط_التحميل") or []))
    dl.append(f"- كتب لها رابط حر: **{has_free}** · للشراء فقط: **{has_buy}** · "
              f"لم تُوثَّق روابطها بعد: **{none_n}**")
    dl.append("")
    for ilm in ULUM:
        if ilm not in by_ilm:
            continue
        dl.append(f"## [{ilm}]({ilm_dirname(ilm)}.md)")
        dl.append("")
        for b in by_ilm[ilm]:
            rd = b.get("روابط_التحميل") or []
            if rd:
                items = []
                for r in rd:
                    tag = "حر" if str(r.get("النوع", "")).strip() == "حر" else "شراء"
                    emoji = "📥" if tag == "حر" else "🛒"
                    items.append(f"{emoji} [{r.get('المصدر', 'رابط')}]({r.get('الرابط', '')})")
                dl.append(f"- **{b['العنوان']}** — {' · '.join(items)}")
            else:
                dl.append(f"- {b['العنوان']} — <sub>لم تُوثَّق بعد</sub>")
        dl.append("")
    dl.append(f"<sub>وُلّد في {datetime.date.today()}</sub>")
    (DOCS / "روابط-التحميل.md").write_text("\n".join(dl) + "\n", encoding="utf-8")

    print(f"✓ وُلّدت {pages} صفحة علم + 5 فهارس ({len(all_books)} كتابًا)")


if __name__ == "__main__":
    main()
