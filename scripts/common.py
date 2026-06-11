# -*- coding: utf-8 -*-
"""ثوابت ودوال مشتركة بين validate.py و build.py — مصدر الحقيقة لأسماء العلوم وترتيبها."""
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"

# القائمة المرتبة للعلوم الـ39 (الاسم القياسي كما يُكتب في حقل «العلم»)
ULUM = [
    "علوم القرآن والقراءات",
    "التفسير",
    "معاجم ألفاظ القرآن",
    "متون الحديث",
    "شروح الحديث",
    "مصطلح الحديث وعلله",
    "الجرح والتعديل وكتب الرجال",
    "العقيدة والفرق والملل",
    "أصول الفقه ومقاصد الشريعة",
    "الفقه",
    "القواعد الفقهية",
    "السيرة النبوية والشمائل",
    "التاريخ الإسلامي والعام",
    "التراجم والطبقات والأنساب",
    "معاجم اللغة",
    "النحو والصرف",
    "البلاغة والنقد الأدبي",
    "الأدب والشعر",
    "التزكية والسلوك والأخلاق",
    "الجغرافيا والبلدان والرحلات",
    "الفهارس والببليوغرافيا التراثية",
    "المراجع المعاصرة المكملة",
    "الفلسفة والمنطق",
    "الطب",
    "الصيدلة والأدوية المفردة",
    "الرياضيات",
    "الفلك وعلم الميقات",
    "الفيزياء والبصريات والحيل",
    "الكيمياء",
    "النبات والحيوان والفلاحة",
    "الموسيقى النظرية",
    "علم العمران والاجتماع",
    "تاريخ العلوم عند العرب والمسلمين",
    "الموسوعات العربية المعاصرة",
    "المراجع الطبية الحديثة بالعربية",
    "مراجع العلوم الطبيعية والهندسة الحديثة بالعربية",
    "مراجع العلوم الإنسانية والاجتماعية الحديثة بالعربية",
    "مراجع القانون والأنظمة بالعربية",
    "معاجم المصطلحات العلمية المجمعية",
]

ANWA_MARJIIYYA = {"شرعية_لغوية", "علمية_تراثية_حضارية", "معاصرة"}
MUSTAWAYAT = {"مبتدئ", "متوسط", "متخصص"}
HALAT_TAWTHIQ = {"موثق", "يحتاج_تحقق"}  # تُقارن بعد تجريد الشدة


def ilm_dirname(ilm: str) -> str:
    """اسم مجلد العلم: الاسم القياسي بشرطات بدل المسافات."""
    return ilm.replace(" ", "-")


def dirname_to_ilm(dirname: str) -> str:
    return dirname.replace("-", " ")


def strip_shadda(s: str) -> str:
    return str(s).replace("ّ", "")


def setup_stdout():
    """ترميز UTF-8 لطرفية ويندوز."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def iter_book_files():
    """كل ملفات الكتب في data/ (يتجاهل ما يبدأ بـ _)."""
    if not DATA.exists():
        return
    for ilm_dir in sorted(DATA.iterdir()):
        if not ilm_dir.is_dir():
            continue
        for f in sorted(ilm_dir.glob("*.yaml")):
            if f.name.startswith("_"):
                continue
            yield ilm_dir, f


def load_book(path: Path):
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_all_books():
    """يحمل كل الكتب؛ يعيد قائمة (مجلد، مسار، بيانات)."""
    out = []
    for ilm_dir, f in iter_book_files():
        out.append((ilm_dir, f, load_book(f)))
    return out
