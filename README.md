# EAR – English Assistance Rote

Materi dan latihan interaktif EAR dalam **satu aplikasi Streamlit**: https://ear-grammar.streamlit.app

| Kelas | Folder materi | Link langsung |
|---|---|---|
| 📘 Grammar | `./week-XX/` | https://ear-grammar.streamlit.app/?kelas=grammar |
| 🗣️ Speaking (101 American English Idioms) | `speaking/week-XX/` | https://ear-grammar.streamlit.app/?kelas=speaking |

Writing dan Listening: coming soon (atur di `tracks.json`).

Semua halaman selalu memakai palet EAR (navy #1E459F, merah #CF2A2A, kuning #FABD32, beige #E1DCCA), juga di HP yang memakai mode gelap.
Setiap week punya 3 sesi (Selasa, Rabu, Jumat): `week-XX/` = Sesi 1, `week-XX/sesi-2/` dan `week-XX/sesi-3/`. Setiap sesi berisi materi, latihan yang langsung dicek (skor tersimpan di HP masing-masing), latihan sentence building, poster PNG, dan PDF worksheet.

Referensi utama: *Grammar for IELTS* (Collins), plus materi tambahan.

## Struktur

```
index.html            daftar semua week
assets/style.css      tampilan bersama
assets/quiz.js        mesin quiz bersama (choice, fill, fix, order, pattern, write)
streamlit_app.py      seluruh kode aplikasi Streamlit (pilihan kelas, silabus, sesi, week terkunci)
speaking/             silabus + materi speaking (week-XX/)
tracks.json           daftar kelas EAR (aktif / coming soon)
syllabus.json         isi silabus 25 week (week tanpa folder tampil terkunci)
.streamlit/config.toml  tema warna Streamlit
week-01/index.html    materi + soal Week 1
week-01/Week1_My_Hobbies_Materi.pdf
```

## Menambah week baru

1. Copy folder `week-01` menjadi `week-02`, lalu ganti isi materi dan array `window.WEEK.sections` (ganti juga `id: "week-02"`).
2. Di `index.html`, set `live: true` pada week tersebut.
3. Poster dibuat terpisah di folder lokal `EAR/Poster` (tidak masuk ke web/GitHub).
4. `git add -A`, `git commit`, `git push`. Streamlit akan otomatis menampilkan week baru dalam 1–2 menit.

## Preview lokal

```bash
streamlit run streamlit_app.py
```

Lalu buka http://localhost:8501

## Publish (Streamlit Community Cloud)

1. Push repo ini ke GitHub.
2. Buka https://share.streamlit.io, login dengan akun GitHub.
3. **Create app** → *Deploy a public app from GitHub* → pilih repo `ear-grammar`, branch `main`, main file `streamlit_app.py`.
4. Isi *App URL*, misalnya `ear-grammar` (jadi `https://ear-grammar.streamlit.app`), lalu **Deploy**.

Halaman HTML juga tetap bisa dipublish lewat GitHub Pages (Settings → Pages → branch `main`, folder `/ (root)`).

## Audio speaking (🔊)

Semua suara di halaman speaking memakai satu suara neural (en-US Jenny) dari file MP3, jadi sama di semua HP.
Setelah membuat atau mengubah teks di `speaking/week-XX/index.html`, buat ulang audionya:

```bash
pip install edge-tts
python tools/make_audio.py speaking/week-02
```

Lalu commit folder `speaking/week-XX/audio/` bersama halamannya.
