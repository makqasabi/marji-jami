# -*- coding: utf-8 -*-
"""يولّد نسخة HTML قابلة للتصفح من مخرجات docs/ وملفات الجذر، بتنسيق عربي RTL.

الاستخدام:  python scripts/html.py
ثم تُفتح docs_html/index.html تلقائيًا في المتصفح.
هذا ملف عرض محلي مولَّد — لا يُحرَّر يدويًا، ومجلد docs_html مستثنى من git.
"""
import re
import sys
import webbrowser
from pathlib import Path

import markdown

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
OUT = ROOT / "docs_html"
ROOT_DOCS = ["README.md", "MANHAJ.md", "CONTRIBUTING.md", "CHANGELOG.md", "STATUS.md"]

TEMPLATE = """<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — المرجع الجامع</title>
<style>
:root {{ --ink:#1f2328; --muted:#656d76; --line:#d0d7de; --accent:#0a7d4b; }}
* {{ box-sizing:border-box; }}
body {{ font-family:"Segoe UI","Tahoma","Geeza Pro","Noto Naskh Arabic",serif;
  line-height:1.95; color:var(--ink); background:#eef0f2; margin:0; }}
.wrap {{ max-width:920px; margin:0 auto; padding:0 22px 90px; background:#fff;
  min-height:100vh; box-shadow:0 0 50px rgba(0,0,0,.05); }}
nav.top {{ position:sticky; top:0; z-index:9; background:#ffffffee; backdrop-filter:blur(6px);
  border-bottom:1px solid var(--line); padding:12px 0; margin-bottom:26px; font-size:14px; }}
nav.top a {{ color:var(--accent); text-decoration:none; margin-left:18px; font-weight:600; }}
nav.top a:hover {{ text-decoration:underline; }}
h1,h2,h3 {{ line-height:1.5; }}
h1 {{ border-bottom:2px solid var(--line); padding-bottom:.3em; }}
h2 {{ margin-top:1.6em; }}
h3 {{ margin-top:2.2em; color:#08603a; border-right:4px solid var(--accent);
  padding-right:12px; }}
a {{ color:#0969da; }}
table {{ border-collapse:collapse; width:100%; margin:1.2em 0; font-size:15px; }}
th,td {{ border:1px solid var(--line); padding:9px 11px; text-align:right; vertical-align:top; }}
th {{ background:#eaf3ee; }}
tr:nth-child(even) td {{ background:#fafcfb; }}
blockquote {{ border-right:4px solid var(--accent); margin:1.2em 0; padding:.4em 18px;
  color:#444; background:#f6faf8; }}
sub {{ color:var(--muted); font-size:12px; }}
code {{ background:#eef1f4; padding:1px 6px; border-radius:5px; font-size:88%;
  direction:ltr; display:inline-block; }}
hr {{ border:none; border-top:1px solid var(--line); margin:2.4em 0; }}
ul {{ padding-right:1.4em; }}
</style>
</head>
<body>
<div class="wrap">
<nav class="top">
<a href="index.html">🏠 الفهرس العام</a>
<a href="فهرس-المؤلفين.html">المؤلفون</a>
<a href="فهرس-القرون.html">القرون</a>
<a href="إحصاءات.html">الإحصاءات</a>
<a href="MANHAJ.html">المنهج</a>
</nav>
{body}
</div>
</body>
</html>
"""

LINK_RE = re.compile(r"\]\(([^)#]+?)\.md(#[^)]*)?\)")


def rewrite_links(text):
    """يحوّل روابط .md إلى .html ويجرّد المسار إلى اسم الملف (docs_html مسطّح)."""
    def repl(m):
        name = m.group(1).replace("\\", "/").split("/")[-1]
        return "](" + name + ".html" + (m.group(2) or "") + ")"
    return LINK_RE.sub(repl, text)


def slugify(value, sep):
    # يطابق scheme الأنكر في build.py: استبدال المسافات بشرطات فقط
    return value.strip().replace(" ", "-")


def convert(src: Path):
    raw = rewrite_links(src.read_text(encoding="utf-8"))
    md = markdown.Markdown(
        extensions=["tables", "sane_lists", "toc"],
        extension_configs={"toc": {"slugify": slugify}},
    )
    html = md.convert(raw)
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
    title = re.sub("<.*?>", "", m.group(1)) if m else src.stem
    return TEMPLATE.format(title=title.strip(), body=html)


def main():
    OUT.mkdir(exist_ok=True)
    files = sorted(DOCS.glob("*.md")) + [ROOT / f for f in ROOT_DOCS if (ROOT / f).exists()]
    for f in files:
        (OUT / (f.stem + ".html")).write_text(convert(f), encoding="utf-8")
    print(f"وُلّد {len(files)} ملف HTML في {OUT}")
    try:
        webbrowser.open((OUT / "index.html").as_uri())
    except Exception:
        print(f"افتح يدويًا: {OUT / 'index.html'}")


if __name__ == "__main__":
    main()
