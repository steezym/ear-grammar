"""EAR Grammar — Streamlit app.

The home page shows the full syllabus (syllabus.json). A week opens once its
folder (week-XX/index.html) exists; the others stay locked. The week pages are
the same static HTML used for GitHub Pages; this app inlines the shared CSS/JS
and renders them inside Streamlit.

To release a new week: add a folder week-02/, week-03/, ... and push.
"""
import json
import re
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent
CSS = (ROOT / "assets" / "style.css").read_text(encoding="utf-8")
JS = (ROOT / "assets" / "quiz.js").read_text(encoding="utf-8")
SYLLABUS = json.loads((ROOT / "syllabus.json").read_text(encoding="utf-8"))
HOME = "🏠 Silabus"

st.set_page_config(page_title="EAR Grammar", page_icon="📚", layout="wide")

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap');
  .stMarkdown, .stButton button, [data-testid="stSidebar"] label p { font-family: "Nunito", sans-serif; }
  .ear-hero { text-align: center; padding: 8px 0 4px; }
  .ear-hero .tag { display: inline-block; background: #CF2A2A; color: #fff; font-weight: 800;
                   padding: 3px 14px; border-radius: 12px; transform: rotate(-3deg); }
  .ear-hero h1 { color: #1E459F; font-size: clamp(34px, 6vw, 54px); font-weight: 900; margin: 8px 0 2px; padding: 0; }
  .ear-hero p { color: #5d6680; margin: 0; }
  .ear-hero .focus { display: inline-block; margin-top: 10px; background: #FABD32; color: #172C5E;
                     padding: 4px 14px; border-radius: 999px; font-weight: 700; }
  .wk-num { font-size: 13px; font-weight: 800; color: #5d6680; letter-spacing: .5px; }
  .wk-badge { display: inline-block; font-size: 11px; font-weight: 800; padding: 1px 8px;
              border-radius: 999px; margin-left: 6px; vertical-align: 1px; }
  .wk-badge.open { background: #FABD32; color: #172C5E; }
  .wk-badge.lock { background: #E1DCCA; color: #5d6680; }
  .wk-topic { font-size: 19px; font-weight: 900; color: #1E459F; line-height: 1.2; margin: 2px 0 4px; }
  .wk-focus { font-size: 14px; font-weight: 700; color: #CF2A2A; margin-bottom: 4px; }
  .wk-act { font-size: 13.5px; color: #5d6680; line-height: 1.4; min-height: 57px; }
  [class*="st-key-open-"] { background: #fff; border-color: #1E459F !important; box-shadow: 0 3px 0 #1E459F; }
  [class*="st-key-locked-"] { background: #F4EFE3; opacity: .72; }
</style>
""", unsafe_allow_html=True)


def released_weeks():
    """Return {number: folder} for every week-XX/index.html."""
    return {int(f.name[-2:]): f for f in sorted(ROOT.glob("week-[0-9][0-9]")) if (f / "index.html").exists()}


def week_label(n):
    topic = next((w["topic"] for w in SYLLABUS if w["week"] == n), "")
    return f"Week {n} · {topic}"


def embed(html):
    """Inline the shared stylesheet and script so the page works inside an iframe."""
    html = re.sub(r'<link rel="stylesheet" href="\.\./assets/style\.css[^"]*">',
                  lambda _: "<style>" + CSS + "</style>", html)
    html = re.sub(r'<script src="\.\./assets/quiz\.js[^"]*"></script>',
                  lambda _: "<script>" + JS + "</script>", html)
    return html.replace("<body>", '<body class="embed">', 1)


def go(label):
    st.session_state.nav = label


released = released_weeks()
options = [HOME] + [week_label(n) for n in released]

with st.sidebar:
    st.markdown("## 📚 EAR Grammar")
    st.caption("English Assistance Rote – Grammar")
    page = st.radio("Menu", options, key="nav")
    st.divider()
    st.caption("Materi baru dibuka setiap minggu. Skor tersimpan di perangkat masing-masing.")


def home():
    st.markdown(f"""
<div class="ear-hero">
  <span class="tag">{len(SYLLABUS)} Weeks</span>
  <h1>EAR Grammar</h1>
  <p>English Assistance Rote: silabus grammar dan latihan interaktif setiap minggu.</p>
  <span class="focus">🔓 {len(released)} dari {len(SYLLABUS)} week sudah dibuka</span>
</div>
""", unsafe_allow_html=True)
    st.write("")

    for i, w in enumerate(SYLLABUS):
        if i % 3 == 0:  # new row each 3 cards, so phones stack them in week order
            cols = st.columns(3)
        n = w["week"]
        is_open = n in released
        with cols[i % 3].container(border=True, key=f"{'open' if is_open else 'locked'}-{n}"):
            badge = '<span class="wk-badge open">OPEN</span>' if is_open else '<span class="wk-badge lock">🔒 LOCKED</span>'
            st.markdown(f"""
<div class="wk-num">WEEK {n}{badge}</div>
<div class="wk-topic">{w['topic']}</div>
<div class="wk-focus">{w['focus'] or '&nbsp;'}</div>
<div class="wk-act">{w['activity']}</div>
""", unsafe_allow_html=True)
            if is_open:
                st.button("Buka materi →", key=f"go-{n}", type="primary", use_container_width=True,
                          on_click=go, args=(week_label(n),))
            else:
                st.button("🔒 Belum dibuka", key=f"go-{n}", disabled=True, use_container_width=True)


def week(n):
    folder = released[n]
    st.iframe(embed((folder / "index.html").read_text(encoding="utf-8")), height=900)

    pdfs = sorted(folder.glob("*.pdf"))
    posters = sorted(folder.glob("*.png"))
    if pdfs or posters:
        st.markdown("### 📥 Download")
        cols = st.columns(2)
        for pdf in pdfs:
            cols[0].download_button("📄 Materi + Worksheet (PDF)", pdf.read_bytes(),
                                    file_name=pdf.name, mime="application/pdf")
        for png in posters:
            cols[1].download_button("🖼️ Poster (PNG)", png.read_bytes(),
                                    file_name=png.name, mime="image/png")
        for png in posters:
            st.image(str(png), caption=f"Poster Week {n}", width=560)
    st.button("← Kembali ke silabus", on_click=go, args=(HOME,))


if page == HOME:
    home()
else:
    week(int(page.split()[1]))
