"""EAR – English Assistance Rote (https://ear-learning.streamlit.app): one Streamlit app for every class.

tracks.json lists the classes. An active class has a folder with syllabus.json and one folder
per released week: week-XX/ is session 1, week-XX/sesi-2/ and sesi-3/ the next meetings.
Weeks without a folder show as locked; classes marked "soon" are listed as coming soon.
The session pages are static HTML; this app inlines the shared CSS/JS/audio and renders them.

All app code lives in this one file on purpose: Streamlit Cloud re-runs the main script on every
update, but can keep a stale copy of an imported local module.
"""
import base64
import json
import re
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent
HOME = "🏠 Silabus"
DAYS = ["Selasa", "Rabu", "Jumat"]  # meetings per week; a syllabus entry can override with "days"

STYLE = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap');
  .stMarkdown, .stButton button, [data-testid="stSidebar"] label p, .stRadio label p { font-family: "Nunito", sans-serif; }
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
  /* class picker as pills; selectors cover both older and newer Streamlit radio markup */
  .st-key-kelas-main, .st-key-kelas-main [data-testid="stRadio"] { width: 100% !important; }
  .st-key-kelas-main [role="radiogroup"] { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; width: 100%; }
  .st-key-kelas-main [role="radiogroup"] > div:not([data-testid]) { display: contents; }
  .st-key-kelas-main label:has(input[type="radio"]) { background: #fff; border: 1.5px solid #E1DCCA; border-radius: 999px;
    padding: 6px 18px !important; margin: 0 !important; cursor: pointer; }
  .st-key-kelas-main label:has(input[type="radio"]:checked) { background: #1E459F; border-color: #1E459F; }
  .st-key-kelas-main label:has(input[type="radio"]:checked) p { color: #fff !important; }
  .st-key-kelas-main label:has(input[type="radio"]) p { font-weight: 800; font-size: 16px; margin: 0; }
  .st-key-kelas-main label div:has(+ [data-testid="stMarkdownContainer"]),
  .st-key-kelas-main [role="radiogroup"] > label > div:first-child { display: none !important; }
  .soon { text-align: center; color: #8a8576; font-size: 14px; margin: 4px 0 6px; }
  .soon span { display: inline-block; border: 1px dashed #c9c2ab; border-radius: 999px; padding: 2px 12px; margin: 2px; }
  .soon.side { text-align: left; margin-top: -6px; }
  .soon.side span { display: block; border: 0; padding: 3px 0 3px 30px; margin: 0; font-size: 15px; }
  .st-key-kelas-side label p { font-weight: 800; }
</style>
"""


def app():
    st.set_page_config(page_title="EAR – English Assistance Rote", page_icon="📚", layout="wide")
    st.markdown(STYLE, unsafe_allow_html=True)

    tracks = json.loads((ROOT / "tracks.json").read_text(encoding="utf-8"))
    active = {t["id"]: t for t in tracks if not t.get("soon")}
    soon = [t for t in tracks if t.get("soon")]

    # The class can come from ?kelas=speaking so a link opens that class directly.
    if st.session_state.get("kelas") not in active:
        wanted = st.query_params.get("kelas", "")
        st.session_state.kelas = wanted if wanted in active else next(iter(active))
    track = active[st.session_state.kelas]
    folder = ROOT / track["folder"]
    syllabus = json.loads((folder / "syllabus.json").read_text(encoding="utf-8"))
    days = {w["week"]: w.get("days", DAYS) for w in syllabus}
    released = sessions_of(folder)
    pages = {session_label(n, k, days[n]): page for n, ss in released.items() for k, page in ss.items()}
    nav_key = "nav-" + track["id"]

    def go(label):
        st.session_state[nav_key] = label

    with st.sidebar:
        st.markdown("## 📚 EAR")
        st.caption("English Assistance Rote")
        class_picker(active, soon, "side")
        st.divider()
        page = st.radio(f"Menu {track['icon']} {track['name']}", [HOME] + list(pages), key=nav_key)
        st.divider()
        st.caption("Materi baru dibuka setiap minggu. Skor tersimpan di perangkat masing-masing.")

    if page == HOME:
        class_picker(active, soon, "main")
        home(track, syllabus, released, days, go)
    else:
        st.iframe(embed(pages[page]), height=900)
        st.button("← Kembali ke silabus", on_click=go, args=(HOME,))


def class_picker(active, soon, where):
    """Class selector; the sidebar ("side") and home page ("main") copies stay in sync via st.session_state.kelas."""
    key = "kelas-" + where
    st.session_state[key] = st.session_state.kelas

    def changed():
        st.session_state.kelas = st.session_state[key]
        st.query_params["kelas"] = st.session_state.kelas

    st.radio("Kelas", list(active), key=key, horizontal=where == "main", on_change=changed,
             format_func=lambda cid: f"{active[cid]['icon']} {active[cid]['name']}",
             label_visibility="collapsed" if where == "main" else "visible")
    if soon:
        st.markdown(f'<div class="soon {where}">' + "".join(
            f"<span>{t['icon']} {t['name']} · coming soon</span>" for t in soon) + "</div>",
            unsafe_allow_html=True)


def sessions_of(folder):
    """{week: {session: page folder}}. week-XX/ holds session 1; week-XX/sesi-2/, sesi-3/, ... the others."""
    weeks = {}
    for week in sorted(folder.glob("week-[0-9][0-9]")):
        found = {k: page for k, page in [(1, week)] + [(k, week / f"sesi-{k}") for k in range(2, 6)]
                 if (page / "index.html").exists()}
        if found:
            weeks[int(week.name[-2:])] = found
    return weeks


def session_label(n, k, days):
    day = days[k - 1] if k <= len(days) else ""
    return f"Week {n} · Sesi {k}" + (f" ({day})" if day else "")


def home(track, syllabus, released, days, go):
    st.markdown(f"""
<div class="ear-hero">
  <span class="tag">{len(syllabus)} Weeks</span>
  <h1>EAR {track['name']}</h1>
  <p>{track['subtitle']}</p>
  <span class="focus">🔓 {len(released)} dari {len(syllabus)} week sudah dibuka</span>
</div>
""", unsafe_allow_html=True)
    st.write("")

    for i, w in enumerate(syllabus):
        if i % 3 == 0:  # new row each 3 cards, so phones stack them in week order
            cols = st.columns(3)
        n = w["week"]
        is_open = n in released
        key = f"{track['id']}-{n}"
        with cols[i % 3].container(border=True, key=("open-" if is_open else "locked-") + key):
            badge = '<span class="wk-badge open">OPEN</span>' if is_open else '<span class="wk-badge lock">🔒 LOCKED</span>'
            st.markdown(f"""
<div class="wk-num">WEEK {n}{badge}</div>
<div class="wk-topic">{w['topic']}</div>
<div class="wk-focus">{w['focus'] or '&nbsp;'}</div>
<div class="wk-act">{w['activity']}</div>
""", unsafe_allow_html=True)
            if is_open:
                latest = max(released[n])
                for k, day in enumerate(days[n], start=1):
                    if k in released[n]:
                        st.button(f"Sesi {k} · {day} →", key=f"go-{key}-{k}", use_container_width=True,
                                  type="primary" if k == latest else "secondary",
                                  on_click=go, args=(session_label(n, k, days[n]),))
                    else:
                        st.button(f"🔒 Sesi {k} · {day}", key=f"go-{key}-{k}", disabled=True, use_container_width=True)
            else:
                st.button("🔒 Belum dibuka", key="go-" + key, disabled=True, use_container_width=True)


def embed(week):
    """Inline the shared stylesheet, script and 🔊 audio so a session page (its folder) works inside an iframe.
    Files are read on every run so edits show up without restarting the app."""
    html = (week / "index.html").read_text(encoding="utf-8")
    css = (ROOT / "assets" / "style.css").read_text(encoding="utf-8")
    js = (ROOT / "assets" / "quiz.js").read_text(encoding="utf-8")
    html = re.sub(r'<link rel="stylesheet" href="(?:\.\./)+assets/style\.css[^"]*">',
                  lambda _: "<style>" + css + "</style>", html)
    html = re.sub(r'<script src="(?:\.\./)+assets/quiz\.js[^"]*"></script>',
                  lambda _: audio_script(week) + "<script>" + js + "</script>", html)
    return html.replace("<body>", '<body class="embed">', 1)


def audio_script(week):
    """window.EAR_AUDIO = {text: data URI} built from week/audio/manifest.json (see tools/make_audio.py)."""
    manifest = week / "audio" / "manifest.json"
    if not manifest.exists():
        return ""
    urls = {text: "data:audio/mpeg;base64," + base64.b64encode((week / "audio" / name).read_bytes()).decode()
            for text, name in json.loads(manifest.read_text(encoding="utf-8")).items()}
    return "<script>window.EAR_AUDIO = " + json.dumps(urls) + ";</script>"


app()
