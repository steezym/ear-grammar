/*
 * Quiz engine shared by every week.
 * A week page defines `window.WEEK = { id, sections: [...] }` and includes this file.
 * Each section renders into <div data-quiz="sectionId"></div>.
 *
 * Item types:
 *   choice : { q, options: [..], answer: index, why }
 *   fill   : { q (use ___ for the blank), answer: [accepted..], why }
 *   fix    : { q (wrong sentence), answer: [accepted corrected sentences..], why }
 *   order  : { words: [..], answer: [accepted sentences..], why }
 *   pattern: { q (prompt), pattern (hint), test: RegExp the sentence must match, model, why }
 *   write  : { q, count, checks: [[label, test, isMistake?]..] }
 *   (test is a RegExp or a function(text) -> bool; isMistake=true means a hit is bad)
 */
(function () {
  const W = window.WEEK;
  if (!W) return;

  const storeKey = "ear-grammar:" + W.id;
  const state = load();
  const graded = []; // keys of auto-graded items

  function load() {
    try { return JSON.parse(localStorage.getItem(storeKey)) || {}; } catch (e) { return {}; }
  }
  function save() {
    try { localStorage.setItem(storeKey, JSON.stringify(state)); } catch (e) { /* storage blocked */ }
  }

  const norm = (s) => s.toLowerCase()
    .replace(/[’']/g, "'")
    .replace(/[.,!?;:"]/g, "")
    .replace(/\s+/g, " ")
    .trim();
  const matches = (input, accepted) => accepted.some((a) => norm(a) === norm(input));

  function el(tag, attrs, ...kids) {
    const n = document.createElement(tag);
    for (const k in attrs || {}) {
      if (k === "class") n.className = attrs[k];
      else if (k === "html") n.innerHTML = attrs[k];
      else if (k.startsWith("on")) n.addEventListener(k.slice(2), attrs[k]);
      else n.setAttribute(k, attrs[k]);
    }
    kids.flat().forEach((c) => c != null && n.append(c));
    return n;
  }

  function feedback(box, ok, item, shown) {
    box.className = "feedback " + (ok ? "right" : "wrong");
    box.innerHTML = (ok ? "✅ Benar!" : "❌ Belum tepat." + (shown ? " Jawaban: <b>" + shown + "</b>" : "")) +
      (item.why ? '<span class="why">💡 ' + item.why + "</span>" : "");
  }

  function record(key, ok) {
    state[key] = ok;
    save();
    updateScore();
  }

  /* ---------- renderers ---------- */

  function renderChoice(item, key, n) {
    const fb = el("div", { class: "feedback" });
    const wrap = el("div", { class: "choices" });
    const parts = item.q.split("___");
    const q = el("div", { class: "qtext" }, el("span", { class: "num" }, n + "."), parts[0], el("u", {}, "      "), parts[1] || "");
    const buttons = item.options.map((opt, i) =>
      el("button", { class: "choice", onclick: () => pick(i) }, opt));
    wrap.append(...buttons);

    function pick(i, silent) {
      const ok = i === item.answer;
      buttons.forEach((b, j) => {
        b.disabled = true;
        if (j === item.answer) b.classList.add("right");
        else if (j === i) b.classList.add("wrong");
      });
      feedback(fb, ok, item);
      if (!silent) record(key, ok);
    }
    if (key in state) pick(state[key + ":v"] ?? item.answer, true);
    buttons.forEach((b, i) => b.addEventListener("click", () => { state[key + ":v"] = i; save(); }));
    return el("div", { class: "ex" }, q, wrap, fb);
  }

  function renderInput(item, key, n, placeholder) {
    const fb = el("div", { class: "feedback" });
    const input = el("input", { type: "text", placeholder, autocomplete: "off", autocapitalize: "off", spellcheck: "false" });
    const btn = el("button", { class: "primary", onclick: check }, "Cek");
    input.addEventListener("keydown", (e) => { if (e.key === "Enter") check(); });
    const q = el("div", { class: "qtext", html: '<span class="num">' + n + ".</span> " + item.q.replace("___", "<u>        </u>") });

    function check(_, silent) {
      if (!input.value.trim()) return;
      const ok = matches(input.value, item.answer);
      input.className = ok ? "right" : "wrong";
      feedback(fb, ok, item, ok ? "" : item.answer[0]);
      if (!silent) { state[key + ":v"] = input.value; record(key, ok); }
    }
    if (state[key + ":v"]) { input.value = state[key + ":v"]; check(null, true); }
    return el("div", { class: "ex" }, q, el("div", { class: "fillrow" }, input, btn), fb);
  }

  function renderOrder(item, key, n) {
    const fb = el("div", { class: "feedback" });
    const pool = el("div", { class: "chips" });
    const built = el("div", { class: "built" });
    const shuffled = item.words.slice();

    function chip(word, i) {
      const c = el("button", { class: "chip", "data-i": i }, word);
      c.addEventListener("click", () => { (c.parentNode === pool ? built : pool).append(c); });
      return c;
    }
    shuffled.forEach((w, i) => pool.append(chip(w, i)));
    const sentence = () => [...built.children].map((c) => c.textContent).join(" ");

    function check(_, silent) {
      if (!built.children.length) return;
      const ok = matches(sentence(), item.answer);
      feedback(fb, ok, item, ok ? "" : item.answer[0]);
      if (!silent) { state[key + ":v"] = [...built.children].map((c) => +c.dataset.i); record(key, ok); }
    }
    function reset() {
      [...built.children].forEach((c) => pool.append(c));
      fb.className = "feedback"; fb.textContent = "";
    }
    if (Array.isArray(state[key + ":v"])) {
      state[key + ":v"].forEach((i) => {
        const c = pool.querySelector('[data-i="' + i + '"]');
        if (c) built.append(c);
      });
      check(null, true);
    }
    return el("div", { class: "ex" },
      el("div", { class: "qtext" }, el("span", { class: "num" }, n + "."), "Ketuk kata sesuai urutan:"),
      pool, built,
      el("div", { class: "fillrow" },
        el("button", { class: "primary", onclick: check }, "Cek"),
        el("button", { class: "ghost", onclick: reset }, "Ulangi")),
      fb);
  }

  function runChecks(text, checks, list) {
    list.innerHTML = "";
    checks.forEach(([label, re, bad]) => {
      const t = text.replace(/[’‘]/g, "'");
      const hit = typeof re === "function" ? re(t) : re.test(t);
      const good = bad ? !hit : hit;
      list.append(el("li", { class: good ? "done" : "miss" }, (good ? "✔ " : "✘ ") + label));
    });
  }

  function renderPattern(item, key, n) {
    const fb = el("div", { class: "feedback" });
    const input = el("input", { type: "text", placeholder: "tulis satu kalimat…", autocomplete: "off", spellcheck: "false" });
    const btn = el("button", { class: "primary", onclick: check }, "Cek");
    input.addEventListener("keydown", (e) => { if (e.key === "Enter") check(); });

    function check(_, silent) {
      if (!input.value.trim()) return;
      const ok = item.test.test(input.value.replace(/[’‘]/g, "'"));
      input.className = ok ? "right" : "wrong";
      feedback(fb, ok, item, ok ? "" : item.model);
      if (!silent) { state[key + ":v"] = input.value; record(key, ok); }
    }
    if (state[key + ":v"]) { input.value = state[key + ":v"]; check(null, true); }
    return el("div", { class: "ex" },
      el("div", { class: "qtext" }, el("span", { class: "num" }, n + "."), item.q),
      el("div", { class: "hint", style: "margin:2px 0 0" }, "Pola: ", el("b", {}, item.pattern)),
      el("div", { class: "fillrow" }, input, btn),
      fb);
  }

  function renderWrite(item, key) {
    const ta = el("textarea", { placeholder: "1. …\n2. …\n3. …", rows: item.count + 2 });
    const list = el("ul", { class: "checklist" });
    ta.value = state[key + ":v"] || "";
    ta.addEventListener("input", () => { state[key + ":v"] = ta.value; save(); });
    return el("div", { class: "ex" },
      el("div", { class: "qtext" }, item.q),
      ta,
      el("div", { class: "fillrow" }, el("button", { class: "primary", onclick: () => runChecks(ta.value, item.checks, list) }, "Cek otomatis")),
      list);
  }

  /* ---------- mount ---------- */

  W.sections.forEach((sec) => {
    const host = document.querySelector('[data-quiz="' + sec.id + '"]');
    if (!host) return;
    sec.items.forEach((item, i) => {
      const key = sec.id + "-" + i;
      const n = i + 1;
      let node;
      if (item.type === "choice") node = renderChoice(item, key, n);
      else if (item.type === "fill") node = renderInput(item, key, n, "ketik jawaban…");
      else if (item.type === "fix") node = renderInput(item, key, n, "tulis kalimat yang benar…");
      else if (item.type === "order") node = renderOrder(item, key, n);
      else if (item.type === "pattern") node = renderPattern(item, key, n);
      else if (item.type === "write") node = renderWrite(item, key);
      if (["choice", "fill", "fix", "order", "pattern"].includes(item.type)) graded.push(key);
      host.append(node);
    });
  });

  function updateScore() {
    const done = graded.filter((k) => k in state).length;
    const right = graded.filter((k) => state[k] === true).length;
    document.querySelectorAll("[data-score]").forEach((n) => { n.textContent = right + " / " + graded.length; });
    document.querySelectorAll("[data-done]").forEach((n) => { n.textContent = done + " / " + graded.length; });
    document.querySelectorAll("[data-bar]").forEach((n) => { n.style.width = (right / graded.length * 100) + "%"; });
    const msg = document.querySelector("[data-msg]");
    if (msg) {
      const pct = right / graded.length;
      msg.textContent = done < graded.length ? "Selesaikan semua soal untuk melihat hasil akhir."
        : pct === 1 ? "Perfect! 🎉 Kamu sudah menguasai materi minggu ini."
        : pct >= 0.7 ? "Great job! 👍 Cek lagi soal yang masih merah."
        : "Keep going! 💪 Baca ulang materinya, lalu coba lagi.";
    }
  }
  updateScore();

  const resetBtn = document.querySelector("[data-reset]");
  if (resetBtn) resetBtn.addEventListener("click", () => {
    if (!confirm("Hapus semua jawaban dan mulai dari awal?")) return;
    try { localStorage.removeItem(storeKey); } catch (e) { /* storage blocked */ }
    location.reload();
  });
})();
