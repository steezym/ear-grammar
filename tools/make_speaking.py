"""Build a speaking session page from a JSON spec (same layout as the Week 1 pages).

Usage:  python tools/make_speaking.py tools/speaking/week-02-sesi-1.json
Writes speaking/week-XX/index.html (sesi 1) or speaking/week-XX/sesi-N/index.html,
then run tools/make_audio.py on that folder to make the 🔊 audio.

In "ex" sentences wrap the idiom in **double stars** (bold); *single stars* make italics.
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def bold(text):
    """**bold** and *italic* markers to HTML."""
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html.escape(text, quote=False))
    return re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)


def plain(text):
    return text.replace("**", "")


def js(value):
    return json.dumps(value, ensure_ascii=False)


def build(spec):
    week, sesi = spec["week"], spec["sesi"]
    folder = ROOT / "speaking" / f"week-{week:02d}"
    if sesi > 1:
        folder = folder / f"sesi-{sesi}"
    up = "../" * (len(folder.relative_to(ROOT).parts))

    cards = []
    for i in spec["idioms"]:
        say_name, say_ex = html.escape(i["idiom"]), html.escape(plain(i["ex"]))
        cards.append(f"""      <div class="idiom">
        <div class="name">{i['emoji']} {html.escape(i['idiom'])} <button data-say="{say_name}">🔊</button><button data-practice="{say_name}" title="Ucapkan">🎤</button></div>
        <div class="mean">{html.escape(i['mean'])}</div>
        <div class="id">{html.escape(i['id'])}</div>
        <div class="ex">{bold(i['ex'])}
          <button data-say="{say_ex}">🔊</button><button data-practice="{say_ex}" title="Ucapkan">🎤</button></div>
      </div>""")

    def choices(items):
        return ",\n".join(f'      {{ type: "choice", q: {js(x["q"])}, options: {js(x["options"])}, answer: {x["answer"]}, why: {js(x["why"])} }}' for x in items)

    speaks = ",\n".join(
        f'      {{ type: "speak", q: {js(s["q"])},\n        model: {js(s["model"])},\n'
        f'        checks: [IDIOM(/{s["regex"]}/i, {js(s["label"])}), LONG] }}' for s in spec["speak"])
    steps = "\n".join(f"        <li>{bold(s)}</li>" for s in spec["roleplay"]["steps"])
    rp = spec["roleplay"]

    page = f"""<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<meta name="theme-color" content="#1e459f">
<title>Speaking Week {week} Sesi {sesi} – {html.escape(spec['title'])} | EAR Speaking</title>
<meta name="description" content="Speaking Week {week} Sesi {sesi}: {html.escape(', '.join(i['idiom'] for i in spec['idioms']))}.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{up}assets/style.css?v=8">
</head>
<body>

<div class="topbar">
  <div class="wrap">
    <a class="home" href="{up}">← EAR Speaking</a>
    <span class="score-pill">Skor: <span data-score>0 / 0</span></span>
  </div>
</div>

<main class="wrap">
  <div class="hero">
    <span class="tag">Speaking · Week {week} · Sesi {sesi}</span>
    <h1>{html.escape(spec['title'])}</h1>
    <p>{html.escape(spec['subtitle'])}</p>
    <span class="focus">{spec['emojis']} Idioms</span>
    <nav class="toc">
      <a href="#idioms">📖 Idioms</a>
      <a href="#practice">🎯 Practice</a>
      <a href="#speaking">🗣️ Speaking</a>
      <a href="#roleplay">🎭 Role-play</a>
      <a href="#result">🏆 Result</a>
    </nav>
  </div>

  <section class="card" id="idioms">
    <h2 class="label y">1. Today's Idioms</h2>
    <p class="hint">Tekan <b>🔊</b> untuk mendengar, lalu tekan <b>🎤</b> dan ucapkan. Web akan memberi skor dan menandai kata yang belum jelas.
      (Mikrofon: pakai <b>Chrome</b> atau <b>Edge</b>, lalu izinkan akses mikrofon.)</p>
    <div class="idioms">
{chr(10).join(cards)}
    </div>
    <div class="note tip"><b>💡 Tips:</b> {bold(spec['tip'])}</div>
  </section>

  <section class="card" id="practice">
    <h2 class="label p">A. What does it mean?</h2>
    <p class="hint">Pilih arti yang tepat.</p>
    <div data-quiz="a"></div>
  </section>

  <section class="card">
    <h2 class="label o">B. Complete the conversation</h2>
    <p class="hint">Pilih idiom yang paling cocok untuk melengkapi percakapan.</p>
    <div data-quiz="b"></div>
  </section>

  <section class="card">
    <h2 class="label r">C. Correct or not?</h2>
    <p class="hint">Apakah idiomnya dipakai dengan benar?</p>
    <div data-quiz="c"></div>
  </section>

  <section class="card" id="speaking">
    <h2 class="label b">D. Speaking practice</h2>
    <p class="hint">Tekan 🔊 untuk mendengar pertanyaan, lalu tekan <b>🎤 Jawab dengan suara</b> dan jawab 2–3 kalimat memakai idiom hari ini. Ketuk lagi kalau sudah selesai; jawabanmu otomatis ditulis dan dicek. Bisa juga diketik manual.</p>
    <div data-quiz="d"></div>
  </section>

  <section class="card" id="roleplay">
    <h2 class="label g">E. Role-play (in class / voice note)</h2>
    <div class="roleplay">
      <b>🎭 Situation:</b> {bold(rp['situation'])}
      <ol>
{steps}
      </ol>
      <p style="margin:8px 0 0">{bold(rp['target'])}</p>
    </div>
  </section>

  <section class="result" id="result">
    <div>Jawaban benar</div>
    <div class="big" data-score>0 / 0</div>
    <div class="bar"><span data-bar></span></div>
    <div>Sudah dikerjakan: <b data-done>0 / 0</b></div>
    <p data-msg style="margin:8px 0 12px"></p>
    <button data-reset>↺ Mulai dari awal</button>
  </section>

  <footer>Small steps, big progress ✨<br>English Assistance Rote – Speaking</footer>
</main>

<script>
const IDIOM = (re, label) => ["Pakai idiom: " + label, re];
const LONG = ["Minimal ±15 kata", (t) => t.trim().split(/\\s+/).length >= 15];

window.WEEK = {{
  id: "speaking-week-{week:02d}-sesi-{sesi}",
  sections: [
    {{ id: "a", items: [
{choices(spec['meaning'])}
    ]}},
    {{ id: "b", items: [
{choices(spec['dialogue'])}
    ]}},
    {{ id: "c", items: [
{choices(spec['correct'])}
    ]}},
    {{ id: "d", items: [
{speaks}
    ]}}
  ]
}};
</script>
<script src="{up}assets/quiz.js?v=8"></script>
</body>
</html>
"""
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "index.html").write_text(page, encoding="utf-8")
    print("wrote", folder.relative_to(ROOT) / "index.html")


if __name__ == "__main__":
    for path in sys.argv[1:]:
        build(json.loads(Path(path).read_text(encoding="utf-8")))
