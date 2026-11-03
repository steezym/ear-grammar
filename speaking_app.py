"""EAR Speaking — Streamlit app (deploy with main file speaking_app.py).

Shows the speaking (idioms) syllabus; a week opens once speaking/week-XX/ exists.
To release a new week: add speaking/week-02/, ... and push.
"""
from ear_app import run

run("speaking", "EAR Speaking",
    "English Assistance Rote: idiom dan latihan speaking setiap minggu (101 American English Idioms).",
    folder="speaking")
