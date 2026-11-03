# EAR – English Assistance Rote

Materi dan latihan interaktif EAR dalam **satu aplikasi Streamlit**: https://ear-grammar.streamlit.app

| Kelas | Folder materi | Link langsung |
|---|---|---|
| 📘 Grammar | `./week-XX/` | https://ear-grammar.streamlit.app/?kelas=grammar |
| 🗣️ Speaking (101 American English Idioms) | `speaking/week-XX/` | https://ear-grammar.streamlit.app/?kelas=speaking |

Writing dan Listening: coming soon (atur di `tracks.json`).

Semua halaman selalu memakai palet EAR (navy #1E459F, merah #CF2A2A, kuning #FABD32, beige #E1DCCA), juga di HP yang memakai mode gelap.
Setiap minggu punya satu halaman web berisi materi, latihan yang langsung dicek (skor tersimpan di HP masing-masing), latihan sentence building, poster PNG, dan PDF worksheet.

Referensi utama: *Grammar for IELTS* (Collins), plus materi tambahan.

## Struktur

```
index.html            daftar semua week
assets/style.css      tampilan bersama
assets/quiz.js        mesin quiz bersama (choice, fill, fix, order, pattern, write)
ear_app.py            kode aplikasi Streamlit (pilihan kelas, silabus, week terkunci)
streamlit_app.py      file utama Streamlit
speaking/             silabus + materi speaking (week-XX/)
tracks.json           daftar kelas EAR (aktif / coming soon)
syllabus.json         isi silabus 25 week (week tanpa folder tampil terkunci)
.streamlit/config.toml  tema warna Streamlit
week-01/index.html    materi + soal Week 1
week-01/week1-poster.png
week-01/Week1_My_Hobbies_Materi.pdf
posters/week-01.html  sumber poster (dirender jadi PNG)
```

## Menambah week baru

1. Copy folder `week-01` menjadi `week-02`, lalu ganti isi materi dan array `window.WEEK.sections` (ganti juga `id: "week-02"`).
2. Di `index.html`, set `live: true` pada week tersebut.
3. Buat poster: copy `posters/week-01.html`, edit, lalu render:

   ```bash
   "C:/Program Files/Google/Chrome/Application/chrome.exe" --headless --hide-scrollbars --virtual-time-budget=4000 --window-size=1254,1254 --screenshot="week-02/week2-poster.png" "file:///C:/.../posters/week-02.html"
   ```

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
