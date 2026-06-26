# -*- coding: utf-8 -*-
"""يولّد بنك أسئلة لعبة «أمهات الكتب» (assets/quiz.js) من بيانات data/.

أنواع الأسئلة: مؤلّف الكتاب · علمه · قرن وفاة مؤلّفه · أيّ كتاب في علمٍ ما ·
محقّق الطبعة المعتمدة · أيّ كتاب لمؤلّفٍ ما. لكلٍّ مستوى صعوبة وشرح.

الاستخدام:  python scripts/build_quiz.py
"""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, ULUM, iter_book_files, load_book, setup_stdout

random.seed(1453)
INSTIT = ("لجنة", "مجموعة", "مجمع", "مكتب", "هيئة", "إدارة", "مركز", "وزارة", "نخبة")


def century(h):
    return (int(h) - 1) // 100 + 1


def good_editor(eds):
    for e in eds or []:
        ed = (e.get("المحقق_أو_المعتني") or "").strip()
        if not ed or ed.startswith("("):
            continue
        if any(w in ed for w in INSTIT):
            continue
        if " " in ed and len(ed) > 5:
            return ed.split("(")[0].strip()
    return None


def pick(pool, answer, n=3):
    opts = [x for x in set(pool) if x and x != answer]
    random.shuffle(opts)
    return opts[:n]


def make(q, answer, distractors, sci, diff, explain):
    if len(distractors) < 3:
        return None
    options = [answer] + distractors[:3]
    random.shuffle(options)
    return {"q": q, "options": options, "answer": options.index(answer),
            "science": sci, "difficulty": diff, "explain": explain}


def main():
    setup_stdout()
    books = []
    for ilm_dir, f in iter_book_files():
        d = load_book(f)
        au = d.get("المؤلف") or {}
        books.append({
            "title": d.get("العنوان", ""), "author": au.get("الاسم", ""),
            "death": au.get("الوفاة_هجري"), "science": d.get("العلم", ""),
            "editor": good_editor(d.get("أفضل_الطبعات")),
        })
    authors = [b["author"] for b in books if b["author"]]
    editors = [b["editor"] for b in books if b["editor"]]
    by_sci = {}
    for b in books:
        by_sci.setdefault(b["science"], []).append(b["title"])

    Q = []
    for b in books:
        t, a, sci = b["title"], b["author"], b["science"]
        # علم الكتاب (سهل)
        q = make(f"إلى أيِّ علمٍ ينتمي كتاب «{t}»؟", sci, pick(ULUM, sci),
                 sci, "سهل", f"«{t}» من {sci}.")
        if q:
            Q.append(q)
        if a and not any(w in a for w in INSTIT):
            # مؤلّف الكتاب (متوسط) — مشتّتات من نفس العلم إن أمكن
            same = [x["author"] for x in books if x["science"] == sci and x["author"] != a]
            dis = pick(same or authors, a)
            q = make(f"من مؤلّف كتاب «{t}»؟", a, dis, sci, "متوسط",
                     f"«{t}» لـ{a}" + (f" (ت {b['death']}هـ)" if b["death"] else "") + ".")
            if q:
                Q.append(q)
            # قرن الوفاة (صعب)
            if b["death"]:
                c = century(b["death"])
                cs = list({century(x["death"]) for x in books if x["death"]})
                dis = pick([f"القرن {x}هـ" for x in cs], f"القرن {c}هـ")
                q = make(f"في أيِّ قرنٍ هجريّ توفّي {a} مؤلّف «{t}»؟", f"القرن {c}هـ",
                         dis, sci, "صعب", f"{a} توفّي سنة {b['death']}هـ (القرن {c}هـ).")
                if q:
                    Q.append(q)
        # محقّق الطبعة (صعب جدًّا)
        if b["editor"]:
            dis = pick(editors, b["editor"])
            q = make(f"من محقّق الطبعة المعتمدة لكتاب «{t}»؟", b["editor"], dis,
                     sci, "صعب جدًّا", f"حقّق «{t}»: {b['editor']}.")
            if q:
                Q.append(q)
    # أيّ كتاب في علمٍ ما (متوسط)
    for sci, titles in by_sci.items():
        if len(titles) < 2:
            continue
        other = [t for s, ts in by_sci.items() if s != sci for t in ts]
        for t in titles[:3]:
            q = make(f"أيُّ هذه الكتب من أمهات علم {sci}؟", t, pick(other, t),
                     sci, "متوسط", f"«{t}» من أمهات {sci}.")
            if q:
                Q.append(q)

    random.shuffle(Q)
    sciences = [s for s in ULUM if s in by_sci]
    payload = {"sciences": sciences, "count": len(Q), "questions": Q}
    (ROOT / "assets" / "quiz.js").write_text(
        "window.QUIZ = " + json.dumps(payload, ensure_ascii=False) + ";\n",
        encoding="utf-8")
    diffs = {}
    for q in Q:
        diffs[q["difficulty"]] = diffs.get(q["difficulty"], 0) + 1
    print(f"✓ assets/quiz.js — {len(Q)} سؤالًا: {diffs}")


if __name__ == "__main__":
    main()
