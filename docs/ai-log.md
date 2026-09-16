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

## Implementasi tutorial form dan data delivery — 16 September 2026

Pemilik meminta seluruh tutorial skeleton, form, dan data delivery diterapkan ke kode, serta meminta diberi tahu untuk bagian di luar akses workspace, seperti PWS, data pribadi, dan Google Drive. Kode awal sudah memiliki form Projects parsial, tetapi model Project dan beberapa import/rute belum tersedia.

Implementasi melanjutkan Projects yang sudah mulai dibuat. Pertanyaan pilihan Projects/Achievements disampaikan karena tutorial menyebut penyesuaian terhadap objek Tugas 2; belum ada jawaban saat implementasi ini dicatat, sehingga pekerjaan dilanjutkan dengan asumsi Projects yang sudah dinyatakan kepada pemilik. Prestasi Achievement yang ada tidak dipindahkan atau dihapus.

Bantuan mencakup penyelesaian template bersama, model/migrasi/admin Project, ModelForm, tambah dan hapus dengan CSRF, pencarian judul, API JSON serta percobaan XML, deserialisasi JSON ke halaman, konfirmasi hapus, pesan sukses, CSS responsif, serta dokumentasi penggunaan. Tautan dan nama contoh disesuaikan dengan informasi Noe Andrew yang sudah ada. Tidak ada isi proyek pribadi atau prestasi baru yang dibuat oleh AI.

Verifikasi lokal:

- `manage.py check`: tidak ada masalah.
- `manage.py makemigrations --check --dry-run`: tidak ada perubahan model tanpa migrasi.
- `manage.py test`: 43 tes lulus, termasuk 28 tes Projects baru.
- Migrasi `0005_project` diterapkan pada SQLite lokal; dua Experience dan dua Achievement yang ada tetap tersimpan.
- `collectstatic --noinput` memperbarui aset lokal.
- Tujuh halaman/endpoint utama mengembalikan HTTP 200 pada database lokal.
- Browser Edge headless dengan database terisolasi: 77 pemeriksaan lulus pada lebar 320, 390, 768, dan 1440 px, mencakup layout, form, pencarian, API, pembatalan konfirmasi, serta hapus dengan pesan sukses. Pemeriksaan visual menemukan teks tombol Cari membungkus; CSS diperbaiki agar teks tombol tetap satu baris.
- Setelah perbaikan CSS, 17 pemeriksaan khusus pencarian dan layout kembali lulus pada keempat lebar layar. Tidak ditemukan error JavaScript; permintaan favicon yang belum tersedia mengembalikan 404. Server dan browser pengujian telah dihentikan.

Deployment PWS, isi proyek pribadi, akses gambar Google Drive, dan pengumpulan tugas belum dilakukan atau diverifikasi. Form publik mengikuti tahap tutorial tanpa autentikasi pemilik; tip kode rahasia pada akhir tutorial merupakan langkah opsional yang belum diaktifkan.
