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
 *   speak  : { q, model (may contain <mark>), checks } — ungraded, with text-to-speech buttons
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

  /* ---------- voice: one neural voice from pre-made MP3s, device voice only as fallback ---------- */

  const normText = (s) => s.replace(/\s+/g, " ").trim();
  const audioUrls = {};  // text -> URL (data: URI inside Streamlit, audio/xxx.mp3 on GitHub Pages)
  if (window.EAR_AUDIO) Object.assign(audioUrls, window.EAR_AUDIO);
  else fetch("audio/manifest.json").then((r) => (r.ok ? r.json() : {})).then((m) => {
    for (const k in m) audioUrls[k] = "audio/" + m[k];
  }).catch(() => { /* no audio for this page */ });
  const player = new Audio();

  function deviceVoice() {
    const rank = (v) => (/natural|neural|online/i.test(v.name) ? 40 : 0) + (/google/i.test(v.name) ? 25 : 0) +
      (/en[-_]US/i.test(v.lang) ? 8 : 0);
    return speechSynthesis.getVoices().filter((v) => /^en[-_]/i.test(v.lang)).sort((a, b) => rank(b) - rank(a))[0];
  }
  function stopVoice() {
    player.pause();
    if ("speechSynthesis" in window) speechSynthesis.cancel();
  }
  function say(text) {
    stopVoice();
    const url = audioUrls[normText(text)];
    if (url) { player.src = url; player.play().catch(() => fallbackSay(text)); }
    else fallbackSay(text);
  }
  function fallbackSay(text) {
    if (!("speechSynthesis" in window)) return;
    const u = new SpeechSynthesisUtterance(text);
    const v = deviceVoice();
    if (v) u.voice = v;
    u.lang = v ? v.lang : "en-US";
    u.rate = 0.95;
    speechSynthesis.speak(u);
  }

  /* ---------- microphone: speech recognition built into Chrome / Edge / Safari ---------- */

  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  let active = null;  // { rec, btn, next }

  // Some browsers (Chrome on Android) repeat earlier words in later results; keep only the longest version.
  function joinResults(results) {
    const parts = [];
    for (const r of results) {
      const t = r[0].transcript.trim();
      if (!t) continue;
      const last = parts[parts.length - 1];
      if (last && t.toLowerCase().startsWith(last.toLowerCase())) parts[parts.length - 1] = t;
      else if (!(last && last.toLowerCase().endsWith(t.toLowerCase()))) parts.push(t);
    }
    return parts.join(" ");
  }

  const MIC_ERRORS = {
    "not-allowed": "Mikrofon belum diizinkan. Ketuk ikon 🔒 di address bar → Microphone → Allow, lalu muat ulang halaman.",
    "service-not-allowed": "Mikrofon belum diizinkan oleh browser. Pakai Google Chrome atau Microsoft Edge.",
    "no-speech": "Tidak ada suara yang terdengar. Ketuk 🎤 lalu langsung bicara, lebih dekat ke mikrofon.",
    "audio-capture": "Mikrofon tidak ditemukan. Pastikan mikrofon terpasang dan tidak dipakai aplikasi lain.",
    "network": "Pengenalan suara butuh internet. Cek koneksi lalu coba lagi."
  };

  // Toggle listening on `btn`; onText(text, done, error) receives the live transcript.
  function listen(btn, opts) {
    if (active) {
      if (active.btn !== btn) active.next = () => listen(btn, opts);  // switch to this button after the old one stops
      active.rec.stop();
      return;
    }
    if (!Recognition) {
      opts.onText("", true, "Browser ini belum mendukung mikrofon. Pakai Google Chrome atau Microsoft Edge.");
      return;
    }
    stopVoice();  // don't record our own 🔊 audio
    const rec = new Recognition();
    rec.lang = "en-US";
    rec.interimResults = true;
    rec.continuous = !!opts.continuous;
    rec.maxAlternatives = 1;
    const label = btn.textContent;
    let text = "", error = "";
    rec.onresult = (e) => { text = joinResults(e.results); opts.onText(text, false); };
    rec.onerror = (e) => { if (e.error !== "aborted") error = MIC_ERRORS[e.error] || "Mikrofon error (" + e.error + "). Coba lagi."; };
    rec.onend = () => {
      const next = active && active.next;
      active = null;
      btn.classList.remove("rec");
      btn.textContent = label;
      opts.onText(text, true, text ? "" : error);
      if (next) next();
    };
    try { rec.start(); } catch (err) {
      opts.onText("", true, "Mikrofon belum bisa dimulai. Tunggu sebentar lalu coba lagi.");
      return;
    }
    active = { rec, btn, next: null };
    btn.classList.add("rec");
    btn.textContent = label.length <= 3 ? "⏹" : "⏹ Selesai bicara";
  }

  const words = (s) => s.toLowerCase().replace(/[’‘]/g, "'").replace(/[^a-z0-9' ]+/g, " ").split(/\s+/).filter(Boolean);

  // Which target words were heard, in order (longest common subsequence).
  function compare(target, heard) {
    const t = words(target), h = words(heard);
    const dp = Array.from({ length: t.length + 1 }, () => new Array(h.length + 1).fill(0));
    for (let i = t.length - 1; i >= 0; i--)
      for (let j = h.length - 1; j >= 0; j--)
        dp[i][j] = t[i] === h[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
    const hit = new Array(t.length).fill(false);
    for (let i = 0, j = 0; i < t.length && j < h.length;) {
      if (t[i] === h[j]) { hit[i] = true; i++; j++; }
      else if (dp[i + 1][j] >= dp[i][j + 1]) i++;
      else j++;
    }
    return { t, hit, score: t.length ? Math.round(hit.filter(Boolean).length / t.length * 100) : 0 };
  }

  // 🎤 buttons with data-practice="sentence": say it, get a pronunciation score.
  document.querySelectorAll("[data-practice]").forEach((btn) => {
    const target = btn.dataset.practice;
    const out = el("div", { class: "practice-result" });
    out.hidden = true;
    btn.parentNode.after(out);
    btn.addEventListener("click", () => listen(btn, {
      onText: (heard, done, error) => {
        out.hidden = false;
        if (error && !heard) { out.innerHTML = '<span class="bad">⚠️ ' + error + "</span>"; return; }
        if (!done) { out.textContent = "🎧 " + heard; return; }
        const r = compare(target, heard);
        const verdict = r.score >= 90 ? "🌟 Excellent!" : r.score >= 70 ? "👍 Good! Hampir sempurna." : "💪 Coba lagi, ucapkan lebih jelas.";
        out.innerHTML = '<div class="score ' + (r.score >= 70 ? "ok" : "bad") + '">' + r.score + "% · " + verdict + "</div>" +
          '<div class="heard">Terdengar: “' + heard.replace(/[<>&]/g, "") + "”</div>" +
          '<div class="target">' + r.t.map((w, i) => '<span class="' + (r.hit[i] ? "w-ok" : "w-miss") + '">' + w + "</span>").join(" ") + "</div>" +
          (r.score < 100 ? '<div class="why">Kata merah belum tertangkap jelas. Dengarkan 🔊 lalu ulangi.</div>' : "");
      }
    }));
  });

  function renderSpeak(item, key, n) {
    const model = el("div", { class: "model", html: item.model });
    model.hidden = true;
    const ta = el("textarea", { placeholder: "Latihan ucapkan dulu, lalu tulis jawabanmu di sini…" });
    const list = el("ul", { class: "checklist" });
    ta.value = state[key + ":v"] || "";
    ta.addEventListener("input", () => { state[key + ":v"] = ta.value; save(); });
    const note = el("div", { class: "feedback" });
    const mic = el("button", { class: "mic" }, "🎤 Jawab dengan suara");
    mic.addEventListener("click", () => listen(mic, {
      continuous: true,
      onText: (heard, done, error) => {
        if (heard) { ta.value = heard; state[key + ":v"] = heard; save(); }
        note.className = "feedback" + (error ? " wrong" : "");
        note.textContent = error || (done ? "" : "🎧 Mendengarkan… ketuk lagi kalau sudah selesai bicara.");
        if (done && heard) runChecks(ta.value, item.checks, list);
      }
    }));
    return el("div", { class: "ex" },
      el("div", { class: "qtext" }, el("span", { class: "num" }, n + "."), item.q),
      el("div", { class: "fillrow" },
        el("button", { onclick: () => say(item.q) }, "🔊 Dengar"),
        el("button", { onclick: () => { model.hidden = !model.hidden; } }, "👀 Contoh jawaban"),
        el("button", { onclick: () => say(model.textContent) }, "🔊 Dengar contoh")),
      model,
      el("div", { class: "fillrow" }, mic), note,
      ta,
      el("div", { class: "fillrow" }, el("button", { class: "primary", onclick: () => runChecks(ta.value, item.checks, list) }, "Cek jawaban")),
      list);
  }

  // Any element with data-say="text" reads that text aloud.
  document.querySelectorAll("[data-say]").forEach((b) => b.addEventListener("click", () => say(b.dataset.say)));

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
      else if (item.type === "speak") node = renderSpeak(item, key, n);
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

  // In-page links scroll smoothly (also works when the page sits in an iframe srcdoc).
  document.querySelectorAll('a[href^="#"]').forEach((a) => a.addEventListener("click", (e) => {
    const target = document.querySelector(a.getAttribute("href"));
    if (target) { e.preventDefault(); target.scrollIntoView({ behavior: "smooth" }); }
  }));

  const resetBtn = document.querySelector("[data-reset]");
  if (resetBtn) resetBtn.addEventListener("click", () => {
    if (!confirm("Hapus semua jawaban dan mulai dari awal?")) return;
    try { localStorage.removeItem(storeKey); } catch (e) { /* storage blocked */ }
    location.reload();
  });
})();
