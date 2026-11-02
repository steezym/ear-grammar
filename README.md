# EAR Grammar

Materi dan latihan interaktif **English Assistance Rote – Grammar** (25 weeks).
Semua halaman selalu memakai palet EAR (navy #1E459F, merah #CF2A2A, kuning #FABD32, beige #E1DCCA), juga di HP yang memakai mode gelap.
Setiap minggu punya satu halaman web berisi materi, latihan yang langsung dicek (skor tersimpan di HP masing-masing), latihan IELTS Speaking, poster PNG, dan PDF worksheet.

Referensi utama: *Grammar for IELTS* (Collins), plus materi tambahan.

## Struktur

```
index.html            daftar semua week
assets/style.css      tampilan bersama
assets/quiz.js        mesin quiz bersama (choice, fill, fix, order, speak, write)
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

## Preview lokal

```bash
python -m http.server 8123
```

Lalu buka http://localhost:8123

## Publish (GitHub Pages)

Repo → **Settings → Pages** → Source: *Deploy from a branch* → Branch `main`, folder `/ (root)`.
Link-nya akan berbentuk `https://<username>.github.io/ear-grammar/`.
