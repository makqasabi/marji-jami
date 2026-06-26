(function () {
  "use strict";
  var Q = (window.QUIZ || { questions: [], sciences: [] });
  var app = document.getElementById("app");
  var hud = document.getElementById("hud");
  var DIFFS = ["الكل", "سهل", "متوسط", "صعب", "صعب جدًّا"];
  var ROUND = 10;
  var state = { diff: "الكل", sci: "", pool: [], i: 0, score: 0, right: 0, wrong: 0 };

  function esc(s) {
    return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
  function shuffle(a) { a = a.slice(); for (var i = a.length - 1; i > 0; i--) { var j = (Math.random() * (i + 1)) | 0; var t = a[i]; a[i] = a[j]; a[j] = t; } return a; }
  function best() { try { return +localStorage.getItem("marji_quiz_best") || 0; } catch (e) { return 0; } }
  function setBest(v) { try { localStorage.setItem("marji_quiz_best", v); } catch (e) {} }

  // ---------- start screen ----------
  function start() {
    hud.hidden = true;
    var b = best();
    var html =
      '<div class="card-pane start">' +
      "<h2>ابدأ التحدّي</h2>" +
      '<p class="sub">' + Q.questions.length + " سؤالًا في أمهات الكتب — اختر المستوى والعلم." +
      (b ? " · أفضل نتيجة لك: <b>" + b + "/" + ROUND + "</b>" : "") + "</p>" +
      '<div class="field"><label>مستوى الصعوبة</label><div class="chips" id="diffs">' +
      DIFFS.map(function (d) { return '<button class="chip' + (d === state.diff ? " on" : "") + '" data-d="' + d + '">' + d + "</button>"; }).join("") +
      "</div></div>" +
      '<div class="field"><label>العلم</label><select id="sci"><option value="">كل العلوم</option>' +
      Q.sciences.map(function (s) { return '<option value="' + esc(s) + '"' + (s === state.sci ? " selected" : "") + ">" + esc(s) + "</option>"; }).join("") +
      "</select></div>" +
      '<button class="btn" id="go">▶ ابدأ الآن</button>' +
      "</div>";
    app.innerHTML = html;
    document.getElementById("diffs").onclick = function (e) {
      var c = e.target.closest("button[data-d]"); if (!c) return;
      state.diff = c.dataset.d;
      [].forEach.call(this.children, function (x) { x.className = "chip" + (x.dataset.d === state.diff ? " on" : ""); });
    };
    document.getElementById("go").onclick = function () {
      state.sci = document.getElementById("sci").value;
      begin();
    };
  }

  // ---------- round ----------
  function begin() {
    var pool = Q.questions.filter(function (q) {
      return (state.diff === "الكل" || q.difficulty === state.diff) &&
             (!state.sci || q.science === state.sci);
    });
    if (pool.length < 1) { alert("لا أسئلة بهذا الاختيار، جرّب غيره."); return; }
    state.pool = shuffle(pool).slice(0, ROUND);
    state.i = 0; state.score = 0; state.right = 0; state.wrong = 0;
    hud.hidden = false;
    document.getElementById("qtot").textContent = state.pool.length;
    document.getElementById("best").textContent = best() ? "أفضل: " + best() : "";
    render();
  }

  function render() {
    var q = state.pool[state.i];
    document.getElementById("qnum").textContent = state.i + 1;
    document.getElementById("score").textContent = state.score;
    var html =
      '<div class="card-pane">' +
      '<div class="qmeta">' + esc(q.science) + " · " + esc(q.difficulty) + "</div>" +
      '<div class="qtext">' + esc(q.q) + "</div>" +
      '<div class="opts" id="opts">' +
      q.options.map(function (o, i) { return '<button class="opt" data-i="' + i + '">' + esc(o) + "</button>"; }).join("") +
      "</div><div id="
      + '"after"></div></div>';
    app.innerHTML = html;
    document.getElementById("opts").onclick = function (e) {
      var btn = e.target.closest(".opt[data-i]"); if (!btn) return;
      answer(+btn.dataset.i);
    };
  }

  function answer(choice) {
    var q = state.pool[state.i];
    var opts = document.querySelectorAll("#opts .opt");
    [].forEach.call(opts, function (b, i) {
      b.disabled = true;
      if (i === q.answer) b.classList.add("correct");
      else if (i === choice) b.classList.add("wrong");
      else b.classList.add("dim");
    });
    if (choice === q.answer) {
      var pts = { "سهل": 1, "متوسط": 2, "صعب": 3, "صعب جدًّا": 4 }[q.difficulty] || 1;
      state.score += pts; state.right++;
      document.getElementById("score").textContent = state.score;
    } else {
      state.wrong++;
    }
    var last = state.i === state.pool.length - 1;
    document.getElementById("after").innerHTML =
      '<div class="explain">' + (choice === q.answer ? "✅ صحيح. " : "❌ ") + esc(q.explain) + "</div>" +
      '<div class="nextrow"><button class="btn" id="next">' + (last ? "النتيجة ←" : "التالي ←") + "</button></div>";
    document.getElementById("next").onclick = function () {
      if (last) { results(); } else { state.i++; render(); }
    };
  }

  // ---------- results ----------
  function results() {
    hud.hidden = true;
    var n = state.pool.length, pct = Math.round(state.right / n * 100);
    var medal = pct >= 90 ? "🥇" : pct >= 70 ? "🥈" : pct >= 50 ? "🥉" : "📚";
    var msg = pct >= 90 ? "إتقانٌ نادر!" : pct >= 70 ? "ممتاز" : pct >= 50 ? "جيّد، واصل" : "ابدأ بالأسهل وستتقن";
    if (state.score > best()) setBest(state.score);
    app.innerHTML =
      '<div class="card-pane results">' +
      '<div class="medal">' + medal + "</div>" +
      '<div class="big">' + state.right + "/" + n + "</div>" +
      '<div class="pct">' + pct + "% · " + state.score + " نقطة · " + esc(msg) + "</div>" +
      '<div class="tally"><span class="ok">✅ صحيح: ' + state.right + '</span><span class="no">❌ خطأ: ' + state.wrong + "</span></div>" +
      '<button class="btn" id="again">↻ جولة جديدة</button>' +
      '<button class="btn ghost" id="home" style="margin-top:10px">⚙ تغيير المستوى/العلم</button>' +
      "</div>";
    document.getElementById("again").onclick = begin;
    document.getElementById("home").onclick = start;
  }

  start();
})();
