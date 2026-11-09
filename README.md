# Portofolio Noe Andrew

Nama : Noe Andrew JM Silalahi

NPM : 2506621440

Kelas : PBP C

### Tugas 1

1. Saya menggunakan elemen semantik HTML5 seperti `header`, `nav`, `main`, `section`, `article`, dan `footer`. Elemen tersebut membantu mengelompokkan isi halaman berdasarkan fungsi, sehingga struktur About Me lebih mudah dibaca, dirawat, dan dipahami oleh browser maupun pengguna yang menggunakan assistive technology. Elemen `section` digunakan untuk memisahkan bagian profil dan focus areas, sedangkan `article` digunakan untuk setiap item yang berdiri sendiri.

2. Tantangan responsive layout yang saya temukan adalah menjaga navbar, foto profil, teks bio, dan tiga item focus areas tetap terbaca pada layar kecil. Saya menggunakan CSS Grid untuk layout utama, kemudian mengubahnya menjadi satu kolom pada breakpoint mobile. Ukuran teks dan jarak navbar juga diperkecil agar menu tidak keluar dari layar atau bertabrakan.

3. Karena website masih static, informasi di dalamnya harus ditulis langsung pada template dan belum dapat dikelola melalui halaman admin atau database. Perubahan achievements, experience, dan focus areas juga masih memerlukan perubahan kode. Pada iterasi berikutnya, saya ingin menambahkan model database dan halaman admin agar konten portfolio dapat diperbarui secara dinamis, serta menambahkan formulir kontak yang dapat memproses pesan.

### Tugas 2

1. Ketika pengguna membuka `/achievements/`, Django membaca `portofolio/urls.py`. Baris `path("", include("main.urls"))` meneruskan pencocokan rute ke `main/urls.py`. Named route `main:show_achievements` memilih fungsi `show_achievements` pada `main/views.py`. View mempersiapkan QuerySet `Achievement.objects.all()` dan memasukkannya ke context dengan nama `achievement_list`. QuerySet dievaluasi ketika datanya diperlukan saat rendering. Django merender `templates/achievements.html`, yang mewarisi kerangka `base.html`. Perulangan `{% for achievement in achievement_list %}` menghasilkan kartu untuk setiap objek; `{% empty %}` menghasilkan pesan ketika tidak ada objek. Hasil HTML dikirim sebagai respons untuk ditampilkan browser. Dengan demikian, URL menentukan tujuan, model mengatur struktur dan akses data, view menyiapkan data, dan template mengatur tampilannya.

2. Data prestasi disimpan pada model supaya judul, deskripsi, penghargaan, gambar, dan urutannya dapat diperbarui melalui admin tanpa mengubah HTML. Satu pola kartu dapat menampilkan banyak objek, sehingga tidak perlu menyalin markup setiap menambah prestasi. Pemisahan ini mengurangi perbedaan struktur antarkartu dan memungkinkan data yang sama digunakan oleh halaman lain atau API pada pengembangan selanjutnya. Field model juga menyediakan tipe data dan aturan validasi yang dapat digunakan oleh form/admin. Template tetap boleh menyimpan teks antarmuka seperti judul halaman dan pesan kosong; yang berasal dari database adalah isi prestasinya. Pengambilan data dan kondisi tampilan dapat diuji terpisah dari perubahan desain CSS.

3. `makemigrations` membuat berkas instruksi perubahan struktur berdasarkan perbedaan model dan riwayat migrasi; perintah ini belum menerapkan perubahan tabel. `migrate` menjalankan instruksi migrasi yang belum diterapkan pada database yang aktif. Contohnya, penambahan model `Achievement` menghasilkan `0003_achievement.py`, kemudian `migrate` membuat tabelnya. Jika kelak ditambah field `organizer = models.CharField(max_length=255, blank=True)`, jalankan `makemigrations main`, tinjau berkas yang dihasilkan, commit berkas tersebut, lalu jalankan `migrate` pada lokal dan deployment. Migrasi data `0004_seed_achievements.py` secara terpisah memasukkan prestasi yang sebelumnya berada di HTML. Menambah satu prestasi lewat admin hanya mengubah isi tabel sehingga tidak memerlukan `makemigrations`.

### Tugas 5

1. Debouncing adalah cara menunda pencarian sampai pengguna berhenti mengetik selama jeda tertentu. Di proyek saya, jedanya 300 ms. Setiap ada input baru, timer sebelumnya dibatalkan dengan `clearTimeout`, lalu dibuat lagi dengan `setTimeout`. Misalnya saya mengetik "React" dengan cepat, pencarian baru dikirim setelah jeda terakhir, sehingga server tidak menerima request untuk setiap huruf. Ini mengurangi jumlah request, beban server, dan pembaruan daftar yang terlalu sering. Debouncing membatalkan timer yang belum berjalan; untuk request yang sudah dikirim, kode saya juga memakai `AbortController` dan mengabaikan respons lama agar hasil pencarian terbaru tidak tertimpa. Menekan Enter tetap menjalankan pencarian langsung. Rujukan: [MDN: Debounce](https://developer.mozilla.org/en-US/docs/Glossary/Debounce).

2. `fetch()` mengembalikan `Promise`, jadi responsnya tidak langsung tersedia. Saya memakai `await fetch(...)` untuk menunggu objek `Response` sebelum memeriksa statusnya. Setelah itu, `await response.json()` menunggu isi respons dibaca dan diubah menjadi data JavaScript. Dua tahap ini berbeda: respons sudah bisa tersedia saat seluruh isinya masih dalam proses diterima. `await` menunda kelanjutan fungsi `async` tersebut, sementara halaman tetap bisa menerima interaksi. Jika saya menulis `const response = fetch(url)` tanpa `await`, request tetap dikirim, tetapi `response` berisi `Promise`. Memanggil `response.json()` langsung akan menghasilkan error karena metode itu milik `Response`. Tanpa `await`, hasilnya masih bisa diproses menggunakan `.then()`. Kode saya juga memeriksa `response.ok`, karena status HTTP seperti 400 atau 500 tidak otomatis membuat `fetch()` menolak Promise. Rujukan: [MDN: Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch) dan [MDN: await](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/await).

3. Cross-Site Scripting (XSS) adalah serangan dengan menyisipkan kode berbahaya ke data yang ditampilkan website, sehingga browser pengguna menjalankannya dalam konteks website tersebut. Penyerang bisa membaca data di halaman atau menjalankan aksi dengan sesi korban. Misalnya, judul proyek berisi `<img src=x onerror=alert('XSS')>` bisa menjalankan JavaScript jika dimasukkan lewat `innerHTML` tanpa perlindungan. Template Django secara default melakukan autoescaping pada variabel yang ditampilkan sebagai HTML, sehingga karakter seperti `<` dan `>` ditampilkan sebagai teks. Data JSON yang dimasukkan ke halaman lewat JavaScript tidak melewati proses itu, jadi perlindungannya harus diterapkan saat memperbarui halaman. Risiko XSS bergantung pada cara data dimasukkan ke DOM. Di proyek saya, judul, deskripsi, dan pesan memakai `textContent` agar tetap menjadi teks; URL dibatasi ke HTTP/HTTPS, dan input form dibersihkan dengan `strip_tags`. Menghapus tag saja belum cukup: data tetap harus ditampilkan dengan aman. Template Django juga perlu dijaga agar data pengguna tidak sembarangan diberi filter `safe`. Rujukan: [Django: perlindungan XSS](https://docs.djangoproject.com/en/5.2/topics/security/#cross-site-scripting-xss-protection) dan [MDN: innerHTML](https://developer.mozilla.org/en-US/docs/Web/API/Element/innerHTML).


# Tugas 6
1. Pengertian REST, RESTful API, serta perbedaan PUT dan PATCH
REST (Representational State Transfer) adalah suatu pendekatan arsitektur dalam pembuatan API yang mengatur bagaimana client dan server berkomunikasi melalui HTTP. REST menggunakan resource sebagai pusat komunikasi, di mana setiap resource memiliki URL atau endpoint tersendiri dan dapat diakses menggunakan HTTP method seperti GET, POST, PUT, PATCH, dan DELETE.

API yang mengembalikan JSON saja belum tentu disebut RESTful karena JSON hanya merupakan format pertukaran data. Sebuah API juga perlu menerapkan prinsip REST, seperti penggunaan resource yang jelas, HTTP method sesuai fungsinya, serta penggunaan status code HTTP yang tepat. Jadi, RESTful API tidak hanya dilihat dari format responsnya, tetapi juga dari cara API mengatur komunikasi antara client dan server.

Perbedaan PUT dan PATCH terletak pada cara keduanya memperbarui data:
- PUT digunakan untuk memperbarui keseluruhan data suatu resource. Biasanya, client mengirimkan seluruh field yang diperlukan.
- PATCH digunakan untuk memperbarui sebagian data saja. Client cukup mengirimkan field yang ingin diubah tanpa harus mengirimkan seluruh data.
Contohnya, ketika ingin mengubah data skill yang memiliki judul, deskripsi, dan kategori:
- Menggunakan PUT: client mengirimkan judul, deskripsi, dan kategori sekaligus.
- Menggunakan PATCH: client hanya mengirimkan judul jika hanya bagian judul yang ingin diubah.
2. Peran Serializer pada Django REST Framework
Serializer pada Django REST Framework berfungsi untuk mengubah data dari model Django menjadi format yang dapat dikirimkan melalui API, seperti JSON. Serializer juga melakukan proses sebaliknya, yaitu menerima data dari client, memvalidasi data tersebut, kemudian mengubahnya menjadi data yang dapat disimpan ke database.

Dibandingkan merakit dictionary secara manual menggunakan JsonResponse seperti pada Tutorial 05, serializer memiliki beberapa keuntungan:
1. Validasi data: Serializer dapat memeriksa apakah data yang dikirimkan sudah sesuai dengan ketentuan sebelum disimpan.
2. Konversi data otomatis: Serializer membantu mengubah objek model Django menjadi data yang dapat dikirimkan dalam format JSON.
3. Mengurangi kode berulang: Kita tidak perlu menyusun dictionary secara manual untuk setiap field.
4. Mengatur field yang dapat diubah: Kita dapat menentukan field yang hanya boleh dibaca (read-only) sehingga client tidak bisa sembarangan mengubahnya.
Dengan demikian, penggunaan serializer membuat pengelolaan data API menjadi lebih terstruktur, konsisten, dan mudah dikembangkan.
3. Perbedaan Autentikasi dan Otorisasi pada Django REST Framework
Autentikasi (authentication) adalah proses untuk memastikan identitas pengguna yang sedang mengakses API. Contohnya, ketika pengguna login menggunakan username dan password, sistem akan memeriksa apakah identitas tersebut benar.

Sementara itu, otorisasi (authorization) adalah proses untuk menentukan tindakan apa saja yang boleh dilakukan oleh pengguna setelah identitasnya diketahui. Misalnya, pengguna biasa hanya boleh melihat data, sedangkan pemilik portfolio memiliki izin untuk menambah, mengubah, dan menghapus data.

Pada Django REST Framework, autentikasi dapat diatur menggunakan authentication class, sedangkan hak akses dapat diatur menggunakan permission class.

Pemeriksaan hak akses harus dilakukan di server menggunakan permission class karena menyembunyikan tombol pada template hanya memengaruhi tampilan antarmuka. Pengguna masih dapat mengakses endpoint secara langsung melalui browser, Postman, atau cara lainnya. Dengan permission class, server tetap memeriksa apakah pengguna memiliki izin sebelum menjalankan suatu tindakan. Hal ini membuat keamanan API tidak hanya bergantung pada tampilan frontend.
4. Pentingnya CSRF pada SessionAuthentication dan Pengujian dengan force_authenticate
CSRF (Cross-Site Request Forgery) merupakan jenis serangan yang memanfaatkan sesi login pengguna untuk mengirimkan permintaan tanpa sepengetahuan pengguna tersebut.

Pada Django REST Framework yang menggunakan SessionAuthentication, identitas pengguna dikenali melalui session cookie yang disimpan oleh browser. Browser dapat mengirimkan cookie tersebut secara otomatis ketika mengakses server. Oleh karena itu, permintaan yang mengubah data, seperti POST, PUT, PATCH, dan DELETE, tetap memerlukan token CSRF untuk memastikan bahwa permintaan tersebut benar-benar berasal dari sumber yang dipercaya.

Token CSRF berfungsi sebagai lapisan perlindungan tambahan agar server dapat memeriksa keabsahan permintaan sebelum memproses perubahan data.

Sementara itu, force_authenticate pada pengujian DRF digunakan untuk membuat pengguna seolah-olah sudah terautentikasi tanpa melalui proses autentikasi session yang sebenarnya. Karena mekanisme ini melewati proses autentikasi normal, pengujian menggunakan force_authenticate tidak cukup untuk membuktikan bahwa perlindungan CSRF berjalan dengan baik.

Untuk menguji CSRF, kita perlu menggunakan APIClient dengan enforce_csrf_checks=True. Dengan cara ini, kita dapat memastikan bahwa permintaan tanpa token CSRF ditolak oleh server, sedangkan permintaan dengan token CSRF yang valid dapat diproses.

AI Disclosure
1. Tools
GPT-6 Luna (VS Code)
2. Prompt Strategy
Merancang Flow Tech Stack dan integrasi webb
Penyusunan Tugas Refleksi
3. Bug fixing: GPT-6 Luna (dalam session VS Code)