"""EAR Grammar — Streamlit app (https://ear-grammar.streamlit.app).

Shows the grammar syllabus; a week opens once its folder week-XX/ exists.
To release a new week: add week-02/, week-03/, ... and push.
"""
from ear_app import run

run("grammar", "EAR Grammar",
    "English Assistance Rote: silabus grammar dan latihan interaktif setiap minggu.",
    folder=".")
