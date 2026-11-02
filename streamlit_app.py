"""EAR Grammar — Streamlit app.

Shows every released week (a folder named week-XX with an index.html).
The week pages are the same static HTML used for GitHub Pages; this app
inlines the shared CSS/JS and renders them inside Streamlit.

To release a new week: add a folder week-02/, week-03/, ... and push.
"""
import re
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).parent
CSS = (ROOT / "assets" / "style.css").read_text(encoding="utf-8")
JS = (ROOT / "assets" / "quiz.js").read_text(encoding="utf-8")

st.set_page_config(page_title="EAR Grammar", page_icon="📚", layout="wide")


def released_weeks():
    """Return [(number, title, folder)] for every week-XX/index.html, in order."""
    weeks = []
    for folder in sorted(ROOT.glob("week-[0-9][0-9]")):
        page = folder / "index.html"
        if not page.exists():
            continue
        html = page.read_text(encoding="utf-8")
        match = re.search(r"<title>(.*?)\s*\|", html)
        title = match.group(1) if match else folder.name
        weeks.append((int(folder.name[-2:]), title, folder))
    return weeks


def embed(html):
    """Inline the shared stylesheet and script so the page works inside an iframe."""
    html = re.sub(r'<link rel="stylesheet" href="\.\./assets/style\.css[^"]*">',
                  lambda _: "<style>" + CSS + "</style>", html)
    html = re.sub(r'<script src="\.\./assets/quiz\.js[^"]*"></script>',
                  lambda _: "<script>" + JS + "</script>", html)
    return html.replace("<body>", '<body class="embed">', 1)


weeks = released_weeks()

with st.sidebar:
    st.markdown("## 📚 EAR Grammar")
    st.caption("English Assistance Rote – Grammar")
    if not weeks:
        st.warning("Belum ada materi.")
        st.stop()
    labels = [title for _, title, _ in weeks]
    choice = st.radio("Pilih minggu", labels, index=len(labels) - 1)
    st.divider()
    st.caption("Materi baru ditambahkan setiap minggu. Skor tersimpan di perangkat masing-masing.")

number, title, folder = weeks[labels.index(choice)]

components.html(embed((folder / "index.html").read_text(encoding="utf-8")),
                height=900, scrolling=True)

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
        st.image(str(png), caption=f"Poster Week {number}", width=560)
