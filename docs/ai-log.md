# Log bantuan AI — 14 September 2026

Log ini merangkum percakapan yang tersedia untuk audit dan penyelesaian checklist portofolio. Ini bukan ekspor lengkap seluruh percakapan atau rekonstruksi sesi sebelumnya.

## Prompt pemilik proyek

1. "sebelum aku lanjut mengerjakan design web saya, pastikan seluruh checklist sudah terpenuhi"
   - Konteks: dokumen Tugas 1, Tugas 2, dan Tutorial 2 diberikan sebagai lampiran.
   - Hasil audit: model baru untuk Tugas 2 belum ada, Achievements masih hard-coded, tiga test gagal, README belum memuat Tugas 2, HTML profil tidak seimbang, dan dua halaman PWS mengembalikan 404.
2. "apakah semua yang belum selesai itu bisa kamu kerjakan semua? bilamana ada yang tidak karena kurang informasi dari saya beritahu, tapi kerjakan dulu yang bisa kamu kerjakan"
   - Keputusan: menggunakan bagian Achievements yang sudah ada sebagai fitur database baru; mempertahankan konten pribadi dan arah desain.
3. Klarifikasi URL LinkedIn: "www.linkedin.com/in/noeandrew".
   - URL dipasang sebagai `https://www.linkedin.com/in/noeandrew`.
4. Klarifikasi status Tutorial 2 di SCELE: "Sudah dikumpulkan".
   - Informasi berasal dari pemilik proyek, tidak diverifikasi melalui akses akun SCELE.

## Bagian yang dibantu Codex

- Model `Achievement`, migrasi struktur dan migrasi data untuk dua prestasi yang sebelumnya tertulis pada template.
- QuerySet pada view dan template dengan perulangan serta pesan kosong.
- Registrasi Achievement pada admin, termasuk pengaturan urutan tampilan.
- Template bersama, perbaikan pasangan tag HTML, tautan kontak, dan CSS untuk layar sempit.
- Penyelarasan bahasa test dengan UI Inggris dan isolasi data seed pada database test.
- Test perilaku Achievement, navigasi, dan profil; dokumentasi setup dan jawaban refleksi Tugas 2.

## Evaluasi hasil dan batasannya

Hasil pemeriksaan lokal setelah implementasi:

- `manage.py check`: tidak ada masalah konfigurasi.
- `manage.py makemigrations --check --dry-run`: tidak ada perubahan model yang belum memiliki migrasi.
- `manage.py test`: 14 test lulus.
- `manage.py showmigrations main`: migrasi `0001` sampai `0004` sudah diterapkan.
- Pemeriksaan browser Edge pada `/`, `/experience/`, dan `/achievements/` di lebar 320, 390, 768, dan 1440 px: seluruh gambar termuat, navigasi aktif sesuai halaman, dan tidak ada overflow horizontal. Judul Achievements juga diperiksa ulang pada 320 px setelah ukuran minimumnya disesuaikan.

Tes tidak hanya memeriksa respons HTTP: tes juga menambahkan beberapa objek, mengubah data, menghapus objek pada database test untuk memeriksa pesan kosong, serta memastikan teks HTML dari data di-escape. Kasus ini membedakan halaman database dari template hard-coded yang sekadar dapat dibuka.

Kebenaran informasi pribadi, pemahaman jawaban refleksi, dan pengumpulan tugas tetap memerlukan keterlibatan pemilik proyek. Log ini tidak mengklaim bahwa pemilik sudah meninjau seluruh kode atau bahwa AI dapat menjamin nilai. Hasil pengecekan kode tidak menggantikan bukti pengumpulan di SCELE.
