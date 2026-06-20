(function () {
  "use strict";
  var D = window.MARJI || { pillars: [], sciences: [], books: [], stats: {} };
  var state = { pillar: null, q: "" };

  var $ = function (s) { return document.querySelector(s); };
  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
  function norm(s) {
    return String(s || "")
      .replace(/[ؐ-ًؚ-ٰٟۖ-ۭـ]/g, "")
      .replace(/[أإآ]/g, "ا").replace(/ى/g, "ي").replace(/ة/g, "ه");
  }

  // ---- stats ----
  var s = D.stats || {};
  $("#stats").innerHTML =
    "<span><b>" + (s.books || 0) + "</b> كتاب</span>" +
    "<span><b>" + (s.sciences || 0) + "</b> علمًا</span>" +
    "<span><b>" + (s.free || 0) + "</b> رابطًا حرًّا</span>";

  // ---- pillar tabs ----
  var nav = $("#pillars");
  function tab(label, val) {
    var b = document.createElement("button");
    b.textContent = label;
    if (state.pillar === val) b.className = "active";
    b.onclick = function () { state.pillar = val; render(); syncTabs(); window.scrollTo(0, 0); };
    b._val = val;
    return b;
  }
  function syncTabs() {
    [].forEach.call(nav.children, function (b) {
      b.className = b._val === state.pillar ? "active" : "";
    });
  }
  nav.appendChild(tab("الكل", null));
  D.pillars.forEach(function (p) { nav.appendChild(tab(p, p)); });

  // ---- search ----
  var searchEl = $("#search");
  var t;
  searchEl.addEventListener("input", function () {
    clearTimeout(t);
    t = setTimeout(function () { state.q = norm(searchEl.value.trim()); render(); }, 120);
  });

  // ---- matching ----
  function matches(b) {
    if (state.pillar && b.pillar !== state.pillar) return false;
    if (!state.q) return true;
    var hay = norm([b.title, b.author, b.science, b.sub, b.why].join(" "));
    return state.q.split(/\s+/).every(function (w) { return hay.indexOf(w) >= 0; });
  }

  function badges(b) {
    var out = "";
    var free = b.links.some(function (l) { return l.type === "حر"; });
    var buy = b.links.some(function (l) { return l.type === "شراء"; });
    if (free) out += '<span class="b free">📥 حر</span>';
    if (buy) out += '<span class="b buy">🛒 شراء</span>';
    if (b.translated) out += '<span class="b tr">📖 مترجَم</span>';
    if (b.modern && !b.translated) out += '<span class="b modern">معاصر</span>';
    if (b.level) out += '<span class="b lvl">' + esc(b.level) + "</span>";
    return out;
  }

  // ---- render list ----
  var content = $("#content");
  function render() {
    var visible = D.books.filter(matches);
    if (!visible.length) {
      content.innerHTML = '<div class="empty">لا نتائج لبحثك.</div>';
      return;
    }
    var bySci = {};
    visible.forEach(function (b) { (bySci[b.science] = bySci[b.science] || []).push(b); });
    var html = "";
    D.sciences.forEach(function (sci) {
      var list = bySci[sci.name];
      if (!list) return;
      html += '<section class="science">';
      html += '<div class="pill-tag">' + esc(sci.pillar) + "</div>";
      html += "<h2>" + esc(sci.name) + ' <span class="n">' + list.length + " كتاب</span></h2>";
      html += '<div class="cards">';
      list.forEach(function (b) {
        var i = D.books.indexOf(b);
        html +=
          '<article class="card" data-i="' + i + '">' +
          "<h3>" + esc(b.title) + "</h3>" +
          '<div class="auth">' + esc(b.author) + "</div>" +
          '<div class="badges">' + badges(b) + "</div>" +
          "</article>";
      });
      html += "</div></section>";
    });
    content.innerHTML = html;
  }

  content.addEventListener("click", function (e) {
    var c = e.target.closest(".card");
    if (c) openDetail(D.books[+c.dataset.i]);
  });

  // ---- detail ----
  var overlay = $("#overlay"), detail = $("#detail");
  function ul(arr) {
    return "<ul>" + arr.map(function (x) { return "<li>" + esc(x) + "</li>"; }).join("") + "</ul>";
  }
  function openDetail(b) {
    var h = "<h2>" + esc(b.title) + "</h2>";
    h += '<div class="d-auth">' + esc(b.author) + (b.sub ? " · " + esc(b.sub) : "") + "</div>";
    h += '<div class="badges">' + badges(b) + "</div>";

    if (b.why) h += "<section><h4>لماذا هو أمٌّ في بابه</h4><p>" + esc(b.why) + "</p></section>";

    if (b.translated && (b.translator || b.translationBody)) {
      h += "<section><h4>الترجمة</h4><p>" +
        (b.translator ? "ترجمة: " + esc(b.translator) : "") +
        (b.translationBody ? " — " + esc(b.translationBody) : "") + "</p></section>";
    }

    if (b.editions && b.editions.length) {
      h += "<section><h4>أفضل الطبعات</h4>";
      b.editions.forEach(function (e) {
        var meta = [e.dar, e.year, e.vols ? e.vols + " مج" : ""].filter(Boolean).join(" · ");
        h += '<div class="ed">' + (e.ed ? '<span class="em">' + esc(e.ed) + "</span> " : "") +
          (meta ? '<span class="meta">' + esc(meta) + "</span>" : "") +
          (e.note ? '<div class="meta">' + esc(e.note) + "</div>" : "") + "</div>";
      });
      h += "</section>";
    }

    if (b.replaces.length) h += "<section><h4>يُغني عن</h4>" + ul(b.replaces) + "</section>";
    if (b.before.length) h += "<section><h4>يُقرأ قبله</h4>" + ul(b.before) + "</section>";
    if (b.commentaries.length) h += "<section><h4>الشروح والمختصرات والذيول</h4>" + ul(b.commentaries) + "</section>";

    if (b.links && b.links.length) {
      h += '<section><h4>القراءة والتحميل</h4><div class="links">';
      b.links.forEach(function (l) {
        var cls = l.type === "حر" ? "free" : l.type === "شراء" ? "buy" : "";
        var icon = l.type === "حر" ? "📥" : l.type === "شراء" ? "🛒" : "🔗";
        h += '<a class="lnk ' + cls + '" href="' + esc(l.url) + '" target="_blank" rel="noopener">' +
          "<span>" + icon + " " + (l.type === "حر" ? "تحميل/قراءة حر" : l.type === "شراء" ? "شراء (نسخة مشروعة)" : "رابط") +
          '</span><span class="src">' + esc(l.src) + "</span></a>";
      });
      h += "</div></section>";
    }

    if (b.critique) h += '<section><h4>ملاحظات نقدية</h4><div class="crit">' + esc(b.critique) + "</div></section>";

    detail.innerHTML = h;
    overlay.hidden = false;
    overlay.querySelector(".sheet").scrollTop = 0;
    document.body.style.overflow = "hidden";
  }
  function closeDetail() { overlay.hidden = true; document.body.style.overflow = ""; }
  $("#closeBtn").onclick = closeDetail;
  overlay.addEventListener("click", function (e) { if (e.target === overlay) closeDetail(); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && !overlay.hidden) closeDetail(); });

  render();
})();
