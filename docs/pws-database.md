# Memperbaiki koneksi database PWS

Error yang dilaporkan pada 23 September 2026:

```text
OperationalError
invalid integer value "<5432>" for connection option "port"
```

Ketiga halaman `/experience/`, `/achievements/`, dan `/projects/` membaca PostgreSQL. Nilai port `<5432>` tidak dapat dipakai untuk koneksi. Halaman About menggunakan context statis sehingga masih dapat dibuka. Traceback ini menunjukkan salah konfigurasi aplikasi, bukan bukti gangguan layanan PWS atau kesalahan navbar.

## Perbaikan pada dashboard

1. Login ke [PWS](https://pws.cs.ui.ac.id), pilih proyek **myportofolio**, lalu buka **Environs** dan **Raw Editor**. Alur pengubahan environment ini dijelaskan dalam [Tutorial 1 PBP](https://pbp.cs.ui.ac.id/en/tutorial/tutorial-1.html#creating-an-account-and-deploying-via-pws-pacil-web-service).
2. Ganti `DB_PORT=<5432>` menjadi `DB_PORT=5432`.
3. Cocokkan seluruh nilai berikut dengan informasi koneksi PostgreSQL milik proyek:

   | Variabel | Nilai yang diperlukan |
   | --- | --- |
   | `PRODUCTION` | `True` |
   | `DB_PORT` | `5432`, sesuai port dalam informasi koneksi |
   | `DB_HOST` | Host database asli, tanpa pembungkus contoh `<...>` |
   | `DB_NAME` | Nama database asli, tanpa pembungkus contoh `<...>` |
   | `DB_USER` | Username database asli, tanpa pembungkus contoh `<...>` |
   | `DB_PASSWORD` | Password database persis seperti yang diberikan; hapus `<...>` hanya jika itu pembungkus contoh, bukan bagian password asli |
   | `SCHEMA` | Nama schema proyek yang sudah digunakan; tutorial memakai `tutorial` |

   Kredensial yang dipakai untuk `git push pws` adalah Project Credentials PWS; isian `DB_*` harus berasal dari informasi koneksi PostgreSQL. Jangan mengganti `PRODUCTION=False` sebagai jalan pintas karena itu memilih database SQLite yang berbeda.
4. Klik **Update All Variables**, kemudian jalankan ulang/redeploy aplikasi agar proses server membaca environment baru. Pantau **Logs** sampai server siap. Saat men-deploy perubahan kode, gunakan langkah commit/push pada bagian deployment README.
5. Buka kembali ketiga URL halaman di atas. Jika muncul error baru, cocokkan dengan tabel berikut.

## Jika error berubah

| Pesan di Logs | Yang diperiksa |
| --- | --- |
| `DB_PORT harus berupa angka...` | Port harus angka 1-65535; contoh `5432`, tanpa `<` dan `>` |
| `DB_... wajib diisi` atau `masih dibungkus <...>` | Isi variabel yang disebutkan dengan nilai asli di Environs |
| `could not translate host name` | Penulisan `DB_HOST`, termasuk pembungkus `<...>`, lalu DNS jika nama sudah benar |
| `password authentication failed` | Kecocokan `DB_USER` dan `DB_PASSWORD` dengan kredensial PostgreSQL |
| `database ... does not exist` | `DB_NAME` |
| `relation ... does not exist` | Database/schema yang dipilih dan status migrasi pada Logs deployment |
| Timeout atau `connection refused` | Host/port dan ketersediaan database; jika informasi koneksi sudah benar, minta pengelola PWS/database memeriksanya |

Jika tabel belum ada, jalankan `python manage.py migrate --noinput` pada lingkungan produksi yang memakai Environs tersebut, atau melalui proses deployment PWS yang menjalankan migrasi. `migrate` di komputer lokal dengan `PRODUCTION=False` hanya memperbarui SQLite lokal.

## Perubahan dalam proyek

- `.env.prod` adalah salinan konfigurasi lokal yang diabaikan Git. Hanya `DB_PORT` diperbaiki menjadi `5432`; nilai lain tetap perlu dicocokkan dengan kredensial asli. File ini tidak otomatis dibaca atau dikirim ke PWS.
- `portofolio/settings.py` membaca `.env` dari root proyek tanpa menimpa environment PWS, memakai port default `5432` bila variabel tidak ada, dan menolak nilai port tidak valid sebelum melayani request.
- Nama database, username, host, password, dan schema diperiksa agar tidak kosong. Pembungkus contoh ditolak untuk nama database, username, host, dan schema. Isi password dipertahankan persis dan tidak dicantumkan dalam pesan validasi.
- `DEBUG=False` ketika `PRODUCTION=True`; detail error produksi dibaca melalui Logs. Ini mengikuti [pengaturan DEBUG Django](https://docs.djangoproject.com/en/5.2/ref/settings/#debug).
- `main/test_settings.py` menguji konfigurasi dengan nilai contoh terisolasi, tanpa menghubungi database produksi. Tes halaman memakai database pengujian tersendiri.

Perbaikan Environs tetap wajib meskipun validasi kode sudah ditambahkan. Keberhasilan tes lokal tidak membuktikan koneksi PostgreSQL produksi sudah pulih.
