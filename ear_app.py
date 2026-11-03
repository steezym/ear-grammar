"""Shared Streamlit app for every EAR class (Grammar, Speaking, ...).

Each class has a syllabus.json and one folder per released week
(week-XX/index.html). Weeks without a folder show as locked on the home page.
The week pages are static HTML; this module inlines the shared CSS/JS and
renders them inside Streamlit.
"""
import json
import re
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent
HOME = "🏠 Silabus"

STYLE = """
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
  .tracks { display: flex; flex-direction: column; gap: 6px; }
  .track { display: flex; align-items: center; gap: 8px; padding: 6px 10px; border-radius: 10px;
           font-weight: 700; font-size: 14px; text-decoration: none !important; color: #172C5E !important; background: #fff; }
  .track.here { background: #1E459F; color: #fff !important; }
  .track.soon { background: transparent; color: #8a8576 !important; border: 1px dashed #c9c2ab; }
  .track small { margin-left: auto; font-size: 11px; font-weight: 800; }
</style>
"""


def run(track_id, title, subtitle, folder):
    """Render the app for one class. `folder` holds syllabus.json and week-XX/ folders."""
    folder = ROOT / folder
    syllabus = json.loads((folder / "syllabus.json").read_text(encoding="utf-8"))
    released = {int(f.name[-2:]): f for f in sorted(folder.glob("week-[0-9][0-9]"))
                if (f / "index.html").exists()}

    st.set_page_config(page_title=title, page_icon="📚", layout="wide")
    st.markdown(STYLE, unsafe_allow_html=True)

    def week_label(n):
        topic = next((w["topic"] for w in syllabus if w["week"] == n), "")
        return f"Week {n} · {topic}"

    def go(label):
        st.session_state.nav = label

    with st.sidebar:
        st.markdown(f"## 📚 {title}")
        st.caption(subtitle)
        page = st.radio("Menu", [HOME] + [week_label(n) for n in released], key="nav")
        st.divider()
        st.markdown("**Kelas EAR**")
        st.markdown(tracks_html(track_id), unsafe_allow_html=True)
        st.divider()
        st.caption("Materi baru dibuka setiap minggu. Skor tersimpan di perangkat masing-masing.")

    if page == HOME:
        home(title, subtitle, syllabus, released, week_label, go)
    else:
        n = int(page.split()[1])
        st.iframe(embed((released[n] / "index.html").read_text(encoding="utf-8")), height=900)
        st.button("← Kembali ke silabus", on_click=go, args=(HOME,))


def tracks_html(current):
    items = []
    for t in json.loads((ROOT / "tracks.json").read_text(encoding="utf-8")):
        label = f'{t["icon"]} {t["name"]}'
        if t["id"] == current:
            items.append(f'<span class="track here">{label}<small>DI SINI</small></span>')
        elif t.get("soon"):
            items.append(f'<span class="track soon">{label}<small>COMING SOON</small></span>')
        elif t["url"]:
            items.append(f'<a class="track" href="{t["url"]}" target="_blank">{label}<small>BUKA ↗</small></a>')
        else:
            items.append(f'<span class="track soon">{label}<small>SEGERA</small></span>')
    return '<div class="tracks">' + "".join(items) + "</div>"


def home(title, subtitle, syllabus, released, week_label, go):
    st.markdown(f"""
<div class="ear-hero">
  <span class="tag">{len(syllabus)} Weeks</span>
  <h1>{title}</h1>
  <p>{subtitle}</p>
  <span class="focus">🔓 {len(released)} dari {len(syllabus)} week sudah dibuka</span>
</div>
""", unsafe_allow_html=True)
    st.write("")

    for i, w in enumerate(syllabus):
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


def embed(html):
    """Inline the shared stylesheet and script so the page works inside an iframe.
    Files are read on every run so edits show up without restarting the app."""
    css = (ROOT / "assets" / "style.css").read_text(encoding="utf-8")
    js = (ROOT / "assets" / "quiz.js").read_text(encoding="utf-8")
    html = re.sub(r'<link rel="stylesheet" href="(?:\.\./)+assets/style\.css[^"]*">',
                  lambda _: "<style>" + css + "</style>", html)
    html = re.sub(r'<script src="(?:\.\./)+assets/quiz\.js[^"]*"></script>',
                  lambda _: "<script>" + js + "</script>", html)
    return html.replace("<body>", '<body class="embed">', 1)
