# -*- coding: utf-8 -*-
"""التحقق من سلامة ملفات data/ وفق مخطط الكتاب في CONTRIBUTING.md.

الاستخدام:  python scripts/validate.py
يخرج برمز 1 عند وجود أخطاء؛ التحذيرات لا توقف البناء.
"""
import datetime
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ANWA_MARJIIYYA, HALAT_TAWTHIQ, MUSTAWAYAT, ULUM,
                    dirname_to_ilm, ilm_dirname, iter_book_files, load_book,
                    setup_stdout, strip_shadda)

REQUIRED = [
    "id", "العنوان", "المؤلف", "العلم", "لماذا_هو_أم_في_بابه",
    "أفضل_الطبعات", "التوافر_الرقمي", "مستوى_القارئ", "نوع_المرجعية",
    "حالة_التوثيق", "مصادر_التوثيق", "آخر_تحديث",
]
ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def word_count(text):
    return len(str(text).split())


def validate_book(path, data, errors, warnings, seen_ids):
    rel = path.relative_to(path.parent.parent.parent)

    def err(msg):
        errors.append(f"{rel}: {msg}")

    def warn(msg):
        warnings.append(f"{rel}: {msg}")

    if not isinstance(data, dict):
        err("الملف ليس قاموس YAML صالحًا")
        return

    for key in REQUIRED:
        if key not in data or data[key] in (None, "", []):
            err(f"الحقل الإلزامي «{key}» مفقود أو فارغ")

    # المعرف
    bid = data.get("id")
    if bid:
        if bid != path.stem:
            err(f"id «{bid}» لا يطابق اسم الملف «{path.stem}»")
        if not ID_RE.match(str(bid)):
            err(f"id «{bid}» ليس kebab-case لاتينيًا")
        if bid in seen_ids:
            err(f"id «{bid}» مكرر (ورد أيضًا في {seen_ids[bid]})")
        else:
            seen_ids[bid] = str(rel)

    # العلم والمجلد
    ilm = data.get("العلم")
    if ilm:
        if ilm not in ULUM:
            err(f"العلم «{ilm}» ليس في قائمة العلوم القياسية (common.py)")
        elif path.parent.name != ilm_dirname(ilm):
            err(f"الملف في مجلد «{path.parent.name}» وحقل العلم «{ilm}» — يجب أن يكون في «{ilm_dirname(ilm)}»")

    # المؤلف
    muallif = data.get("المؤلف")
    nau = data.get("نوع_المرجعية")
    if isinstance(muallif, dict):
        if not muallif.get("الاسم"):
            err("المؤلف.الاسم مفقود")
        hay2a = muallif.get("هيئة") in ("نعم", True)
        muasir = muallif.get("معاصر") in ("نعم", True)
        wh = muallif.get("الوفاة_هجري")
        wm = muallif.get("الوفاة_ميلادي")
        if not (hay2a or muasir):
            if not isinstance(wh, int):
                err("المؤلف.الوفاة_هجري مفقود أو ليس رقمًا (للهيئات/الأحياء أضف هيئة: نعم أو معاصر: نعم)")
            if not isinstance(wm, int):
                err("المؤلف.الوفاة_ميلادي مفقود أو ليس رقمًا")
        if isinstance(wh, int) and not (1 <= wh <= 1500):
            err(f"الوفاة_هجري {wh} خارج النطاق المعقول")
        if isinstance(wm, int) and not (570 <= wm <= 2100):
            err(f"الوفاة_ميلادي {wm} خارج النطاق المعقول")
    elif muallif is not None:
        err("المؤلف يجب أن يكون قاموسًا (الاسم، الوفاة_هجري…)")

    # فقرة المنزلة
    limadha = data.get("لماذا_هو_أم_في_بابه")
    if limadha:
        wc = word_count(limadha)
        if wc < 40:
            err(f"«لماذا_هو_أم_في_بابه» قصيرة جدًا ({wc} كلمة؛ المطلوب 80–150)")
        elif not (80 <= wc <= 180):
            warn(f"«لماذا_هو_أم_في_بابه» {wc} كلمة (المستهدف 80–150)")

    # الطبعات
    tabaat = data.get("أفضل_الطبعات")
    if isinstance(tabaat, list) and tabaat:
        for i, t in enumerate(tabaat, 1):
            if not isinstance(t, dict):
                err(f"الطبعة {i} ليست قاموسًا")
                continue
            if not t.get("الدار"):
                err(f"الطبعة {i}: «الدار» مفقودة")
            halat = strip_shadda(data.get("حالة_التوثيق", ""))
            if not t.get("المحقق_أو_المعتني") and not t.get("السنة") and halat == "موثق":
                warn(f"الطبعة {i}: بلا محقق ولا سنة رغم أن الحالة «موثّق»")
    elif tabaat is not None and not isinstance(tabaat, list):
        err("أفضل_الطبعات يجب أن تكون قائمة")

    # التوافر الرقمي
    tawafur = data.get("التوافر_الرقمي")
    if tawafur is not None and not isinstance(tawafur, dict):
        err("التوافر_الرقمي يجب أن يكون قاموسًا")
    elif isinstance(tawafur, dict) and "المكتبة_الشاملة" not in tawafur:
        warn("التوافر_الرقمي بلا حقل «المكتبة_الشاملة»")

    # روابط التحميل (حقل اختياري)
    rd = data.get("روابط_التحميل")
    if rd is not None:
        if not isinstance(rd, list):
            err("روابط_التحميل يجب أن تكون قائمة")
        else:
            for i, r in enumerate(rd, 1):
                if not isinstance(r, dict):
                    err(f"رابط التحميل {i} ليس قاموسًا")
                    continue
                if not r.get("الرابط"):
                    err(f"رابط التحميل {i}: «الرابط» مفقود")
                if str(r.get("النوع", "")).strip() not in ("حر", "شراء"):
                    err(f"رابط التحميل {i}: «النوع» يجب أن يكون «حر» أو «شراء»")

    # القيم المعدودة
    mustawa = data.get("مستوى_القارئ")
    if mustawa:
        parts = [p.strip() for p in str(mustawa).split("/")]
        bad = [p for p in parts if p not in MUSTAWAYAT]
        if bad:
            err(f"مستوى_القارئ يحوي قيمًا غير قياسية: {bad} (المسموح: مبتدئ/متوسط/متخصص)")

    if nau and nau not in ANWA_MARJIIYYA:
        err(f"نوع_المرجعية «{nau}» غير قياسي (المسموح: {sorted(ANWA_MARJIIYYA)})")
    if nau in ("علمية_تراثية_حضارية", "معاصرة") and not data.get("ملاحظات_نقدية"):
        err(f"«ملاحظات_نقدية» إلزامية لنوع المرجعية «{nau}»")

    halat = data.get("حالة_التوثيق")
    if halat and strip_shadda(halat) not in HALAT_TAWTHIQ:
        err(f"حالة_التوثيق «{halat}» غير قياسية (المسموح: موثّق / يحتاج_تحقق)")

    # التاريخ
    tahdith = data.get("آخر_تحديث")
    if tahdith is not None and not isinstance(tahdith, (datetime.date, datetime.datetime)):
        err(f"آخر_تحديث «{tahdith}» ليس تاريخًا بصيغة YYYY-MM-DD")


def main():
    setup_stdout()
    errors, warnings, seen_ids = [], [], {}
    count = 0
    for ilm_dir, f in iter_book_files():
        count += 1
        if dirname_to_ilm(ilm_dir.name) not in ULUM:
            errors.append(f"data/{ilm_dir.name}: اسم المجلد لا يقابل علمًا في القائمة القياسية")
        try:
            data = load_book(f)
        except Exception as e:
            errors.append(f"{f.name}: خطأ في قراءة YAML — {e}")
            continue
        validate_book(f, data, errors, warnings, seen_ids)

    for w in warnings:
        print(f"⚠ تحذير: {w}")
    for e in errors:
        print(f"✗ خطأ: {e}")
    print(f"\nفُحص {count} ملفًا — أخطاء: {len(errors)}، تحذيرات: {len(warnings)}")
    if errors:
        sys.exit(1)
    print("✓ كل الملفات سليمة")


if __name__ == "__main__":
    main()
