<!-- @format -->

# Dokumentasi Tabel Database

Dokumentasi lengkap untuk setiap tabel beserta field-field dan kegunaannya dalam sistem Prediksi Pendapatan Pajak Kendaraan Bermotor di UPPD/SAMSAT Jayapura.

---

## 📋 Daftar Isi

1. [Tabel Referensi](#tabel-referensi)
   - [Kecamatan](#1-tabel-kecamatan)
   - [Kelurahan](#2-tabel-kelurahan)
   - [Jenis Kendaraan](#3-tabel-jenis-kendaraan)
   - [Merek Kendaraan](#4-tabel-merek-kendaraan)
   - [Type Kendaraan](#5-tabel-type-kendaraan)
2. [Tabel Data Utama](#tabel-data-utama)
   - [Wajib Pajak](#6-tabel-wajib-pajak)
   - [Kendaraan Bermotor](#7-tabel-kendaraan-bermotor)
   - [Data Pajak Kendaraan](#8-tabel-data-pajak-kendaraan)
   - [Transaksi Pajak](#9-tabel-transaksi-pajak)
3. [Tabel Agregat dan Prediksi](#tabel-agregat-dan-prediksi)
   - [Agregat Pendapatan Bulanan](#10-tabel-agregat-pendapatan-bulanan)
   - [Hasil Prediksi](#11-tabel-hasil-prediksi)

---

## 📊 Tabel Referensi

Tabel-tabel referensi berfungsi sebagai master data yang digunakan oleh tabel-tabel utama. Data dalam tabel referensi bersifat statis dan jarang berubah, namun sangat penting untuk menjaga konsistensi data di seluruh sistem.

---

### 1. Tabel Kecamatan

Tabel `kecamatan` digunakan untuk menyimpan data kecamatan yang berada di wilayah kerja UPPD/SAMSAT Jayapura. Tabel ini berfungsi sebagai referensi geografis tingkat pertama dalam sistem, dimana setiap kecamatan memiliki nama yang unik dan terindeks untuk mempercepat pencarian data. Tabel ini menjadi dasar untuk pembagian wilayah administratif yang lebih detail, yaitu kelurahan.

Field `id` merupakan primary key yang secara otomatis di-generate oleh sistem sebagai identifier unik untuk setiap kecamatan. Field `nama` menyimpan nama kecamatan dengan panjang maksimal 100 karakter, dimana setiap nama harus unik dalam sistem dan memiliki index untuk optimasi query. Contoh nama kecamatan yang dapat disimpan adalah "Abepura", "Jayapura Selatan", "Jayapura Utara", dan sebagainya.

Relasi yang dimiliki tabel ini adalah one-to-many dengan tabel `kelurahan`, dimana satu kecamatan dapat memiliki banyak kelurahan. Ketika sebuah kecamatan dihapus, semua kelurahan yang terkait juga akan ikut terhapus karena menggunakan cascade delete. Tabel ini diurutkan berdasarkan nama kecamatan secara alfabetis untuk memudahkan pencarian dan tampilan data.

---

### 2. Tabel Kelurahan

Tabel `kelurahan` menyimpan data kelurahan atau desa yang berada di bawah wilayah kecamatan. Tabel ini berfungsi sebagai referensi geografis tingkat kedua dalam sistem, dimana setiap kelurahan harus terhubung dengan satu kecamatan tertentu. Kombinasi antara kecamatan dan nama kelurahan harus unik dalam sistem, sehingga tidak mungkin ada dua kelurahan dengan nama yang sama dalam satu kecamatan.

Field `id` merupakan primary key yang di-generate otomatis sebagai identifier unik. Field `kecamatan` merupakan foreign key yang menghubungkan kelurahan dengan tabel kecamatan, menggunakan cascade delete sehingga ketika kecamatan dihapus, semua kelurahan terkait juga terhapus. Field `nama` menyimpan nama kelurahan dengan panjang maksimal 100 karakter dan memiliki index untuk mempercepat pencarian.

Tabel ini digunakan sebagai referensi lokasi untuk data wajib pajak, dimana setiap wajib pajak dapat dikaitkan dengan kelurahan tertentu untuk keperluan administrasi dan pelaporan. Data kelurahan diurutkan berdasarkan nama secara alfabetis, dan ketika ditampilkan akan menampilkan format "Nama Kelurahan, Nama Kecamatan" untuk memberikan konteks geografis yang jelas.

---

### 3. Tabel Jenis Kendaraan

Tabel `jenis_kendaraan` berfungsi sebagai master data untuk mengklasifikasikan berbagai jenis kendaraan bermotor yang terdaftar dalam sistem. Tabel ini menyimpan informasi tentang jenis kendaraan seperti "Honda Beat", "Toyota Avanza", "Yamaha NMAX", dan sebagainya. Setiap jenis kendaraan memiliki nama yang unik dan dikategorikan ke dalam salah satu kategori yang telah ditentukan.

Field `id` merupakan primary key yang di-generate otomatis. Field `nama` menyimpan nama jenis kendaraan dengan panjang maksimal 100 karakter, harus unik dalam sistem, dan memiliki index untuk optimasi query. Field `kategori` merupakan field pilihan yang mengklasifikasikan jenis kendaraan ke dalam kategori tertentu, yaitu "MOTOR" untuk sepeda motor, "MOBIL" untuk mobil penumpang, "JEEP" untuk kendaraan jeep, "TRUK" untuk truk, "BUS" untuk bus, dan "LAINNYA" untuk kategori lainnya. Default kategori adalah "MOTOR" jika tidak ditentukan.

Tabel ini digunakan sebagai referensi oleh tabel `kendaraan_bermotor` untuk mengidentifikasi jenis kendaraan yang dimiliki oleh setiap wajib pajak. Selain itu, tabel ini juga digunakan oleh tabel `agregat_pendapatan_bulanan` dan `hasil_prediksi` untuk melakukan agregasi dan prediksi berdasarkan jenis kendaraan tertentu. Data diurutkan berdasarkan nama jenis kendaraan secara alfabetis.

---

### 4. Tabel Merek Kendaraan

Tabel `merek_kendaraan` menyimpan data merek atau brand kendaraan bermotor yang terdaftar dalam sistem. Tabel ini berfungsi sebagai master data untuk mengidentifikasi berbagai merek kendaraan seperti "Honda", "Toyota", "Yamaha", "Suzuki", dan sebagainya. Setiap merek memiliki nama yang unik dalam sistem.

Field `id` merupakan primary key yang di-generate otomatis sebagai identifier unik. Field `nama` menyimpan nama merek kendaraan dengan panjang maksimal 100 karakter, harus unik dalam sistem, dan memiliki index untuk mempercepat pencarian data. Contoh nama merek yang dapat disimpan adalah "Honda", "Yamaha", "Toyota", "Daihatsu", dan sebagainya.

Tabel ini tidak langsung terhubung dengan tabel `kendaraan_bermotor`, melainkan terhubung melalui tabel `type_kendaraan`. Relasi yang dimiliki adalah one-to-many dengan tabel `type_kendaraan`, dimana satu merek dapat memiliki banyak type kendaraan. Sebagai contoh, merek "Honda" dapat memiliki type seperti "Beat", "Vario", "PCX", dan sebagainya. Ketika sebuah merek dihapus, semua type kendaraan yang terkait juga akan terhapus karena menggunakan cascade delete. Data diurutkan berdasarkan nama merek secara alfabetis.

---

### 5. Tabel Type Kendaraan

Tabel `type_kendaraan` menyimpan data type atau model spesifik dari kendaraan bermotor yang terhubung dengan merek tertentu. Tabel ini berfungsi sebagai master data yang menghubungkan antara merek kendaraan dengan type spesifiknya, seperti "Honda Beat", "Yamaha NMAX", "Toyota Avanza", dan sebagainya. Kombinasi antara merek dan nama type harus unik dalam sistem.

Field `id` merupakan primary key yang di-generate otomatis. Field `merek` merupakan foreign key yang menghubungkan type kendaraan dengan tabel `merek_kendaraan`, menggunakan cascade delete sehingga ketika merek dihapus, semua type terkait juga terhapus. Field `nama` menyimpan nama type kendaraan dengan panjang maksimal 200 karakter dan memiliki index untuk optimasi query.

Tabel ini digunakan sebagai referensi oleh tabel `kendaraan_bermotor` untuk mengidentifikasi type spesifik dari setiap kendaraan yang terdaftar. Dengan struktur ini, sistem dapat mengakses informasi merek kendaraan melalui relasi `type_kendaraan.merek`, sehingga tidak perlu menyimpan data merek secara langsung di tabel kendaraan bermotor. Data diurutkan berdasarkan merek terlebih dahulu, kemudian berdasarkan nama type secara alfabetis. Ketika ditampilkan, format yang digunakan adalah "Nama Merek - Nama Type", misalnya "Honda - Beat".

---

## 🚗 Tabel Data Utama

Tabel-tabel data utama menyimpan informasi transaksional dan data operasional yang menjadi inti dari sistem. Data dalam tabel-tabel ini sering berubah seiring dengan aktivitas operasional UPPD/SAMSAT.

---

### 6. Tabel Wajib Pajak

Tabel `wajib_pajak` menyimpan data pemilik kendaraan bermotor yang terdaftar dalam sistem pajak kendaraan. Tabel ini merupakan tabel utama yang berisi informasi identitas dan alamat dari setiap wajib pajak yang memiliki kendaraan bermotor. Setiap wajib pajak dapat memiliki lebih dari satu kendaraan bermotor.

Field `id` merupakan primary key yang di-generate otomatis. Field `kelurahan` merupakan foreign key yang menghubungkan wajib pajak dengan tabel `kelurahan`, bersifat opsional (dapat null) dan menggunakan protect delete untuk mencegah penghapusan kelurahan yang masih memiliki wajib pajak. Field `no_ktp` menyimpan nomor KTP wajib pajak dengan panjang maksimal 50 karakter, bersifat opsional, dan memiliki index untuk mempercepat pencarian. Field `nama` menyimpan nama lengkap wajib pajak dengan panjang maksimal 200 karakter dan memiliki index untuk optimasi query. Field `alamat` menyimpan alamat lengkap wajib pajak dalam bentuk text tanpa batasan panjang karakter.

Field `created_at` menyimpan timestamp kapan data wajib pajak pertama kali dibuat dalam sistem, diisi otomatis saat record pertama kali disimpan. Field `updated_at` menyimpan timestamp kapan data wajib pajak terakhir kali diupdate, diupdate otomatis setiap kali record dimodifikasi. Tabel ini memiliki index tambahan pada field `no_ktp` dan `nama` untuk mempercepat pencarian berdasarkan identitas wajib pajak.

Relasi yang dimiliki tabel ini adalah one-to-many dengan tabel `kendaraan_bermotor`, dimana satu wajib pajak dapat memiliki banyak kendaraan bermotor. Ketika wajib pajak dihapus, sistem akan mencegah penghapusan jika masih ada kendaraan yang terdaftar dengan menggunakan protect delete. Tabel ini menjadi dasar untuk semua transaksi pajak kendaraan dalam sistem.

---

### 7. Tabel Kendaraan Bermotor

Tabel `kendaraan_bermotor` merupakan tabel inti yang menyimpan data detail dari setiap kendaraan bermotor yang terdaftar dalam sistem. Tabel ini menghubungkan informasi kendaraan dengan pemiliknya (wajib pajak), jenis kendaraan, dan type kendaraan. Setiap kendaraan memiliki nomor polisi yang unik sebagai identifier utama.

Field `id` merupakan primary key yang di-generate otomatis. Field `jenis` merupakan foreign key yang menghubungkan kendaraan dengan tabel `jenis_kendaraan`, menggunakan protect delete untuk mencegah penghapusan jenis kendaraan yang masih digunakan. Field `type_kendaraan` merupakan foreign key yang menghubungkan kendaraan dengan tabel `type_kendaraan`, dimana melalui relasi ini sistem dapat mengakses informasi merek kendaraan. Field `wajib_pajak` merupakan foreign key yang menghubungkan kendaraan dengan pemiliknya di tabel `wajib_pajak`, menggunakan protect delete.

Field `no_polisi` menyimpan nomor polisi kendaraan dengan panjang maksimal 20 karakter, harus unik dalam sistem, dan memiliki index untuk mempercepat pencarian. Field `no_rangka` menyimpan nomor rangka kendaraan dengan panjang maksimal 50 karakter, harus unik dalam sistem, dan memiliki index. Field `no_mesin` menyimpan nomor mesin kendaraan dengan panjang maksimal 100 karakter dan memiliki index.

Field `tahun_buat` menyimpan tahun pembuatan kendaraan dengan validasi antara tahun 1900 hingga 2100, dan memiliki index untuk analisis berdasarkan umur kendaraan. Field `jml_cc` menyimpan kapasitas mesin kendaraan dalam satuan CC (Cubic Centimeter). Field `bbm` menyimpan jenis bahan bakar kendaraan dengan pilihan "BENSIN" untuk bensin, "SOLAR" untuk solar, "LISTRIK" untuk kendaraan listrik, dan "HYBRID" untuk kendaraan hybrid.

Field `created_at` menyimpan timestamp kapan data kendaraan pertama kali dibuat, dan `updated_at` menyimpan timestamp kapan data terakhir kali diupdate. Tabel ini memiliki beberapa index untuk optimasi query, yaitu index pada `no_polisi`, `no_rangka`, kombinasi `wajib_pajak` dan `tahun_buat`, kombinasi `jenis` dan `type_kendaraan`, serta index pada `tahun_buat`.

Tabel ini memiliki relasi one-to-one dengan tabel `data_pajak_kendaraan` untuk menyimpan informasi pajak terkini, dan one-to-many dengan tabel `transaksi_pajak` untuk menyimpan riwayat pembayaran pajak. Tabel ini juga memiliki property `njkb_saat_ini` dan `dp_pkb_saat_ini` yang mengambil data dari tabel `data_pajak_kendaraan` untuk kemudahan akses. Ketika kendaraan disimpan, sistem akan otomatis menghitung ulang dasar pengenaan PKB jika ada perubahan pada data pajak.

---

### 8. Tabel Data Pajak Kendaraan

Tabel `data_pajak_kendaraan` menyimpan informasi pajak terkini untuk setiap kendaraan bermotor. Tabel ini memiliki relasi one-to-one dengan tabel `kendaraan_bermotor`, dimana setiap kendaraan hanya memiliki satu record data pajak. Data dalam tabel ini dapat berubah setiap kali terjadi transaksi pembayaran pajak yang mengubah nilai NJKB atau parameter pajak lainnya.

Field `id` merupakan primary key yang di-generate otomatis. Field `kendaraan` merupakan foreign key one-to-one yang menghubungkan data pajak dengan kendaraan, menggunakan cascade delete sehingga ketika kendaraan dihapus, data pajaknya juga terhapus.

Field `njkb_saat_ini` menyimpan Nilai Jual Kendaraan Bermotor (NJKB) terkini dengan presisi 15 digit dan 2 desimal, default 0. NJKB merupakan nilai dasar yang digunakan untuk menghitung pajak kendaraan. Field `bobot_saat_ini` menyimpan bobot kendaraan dengan presisi 5 digit dan 2 desimal, default 1.0. Bobot ini digunakan sebagai faktor pengali untuk menghitung dasar pengenaan PKB.

Field `dp_pkb_saat_ini` menyimpan Dasar Pengenaan Pajak Kendaraan Bermotor (DP PKB) dengan presisi 15 digit dan 2 desimal, default 0. Field ini dihitung otomatis oleh sistem dengan mengalikan `njkb_saat_ini` dengan `bobot_saat_ini` setiap kali data disimpan. Field `tarif_pkb_saat_ini` menyimpan tarif PKB dalam persen dengan presisi 5 digit dan 2 desimal, default 0.

Field `created_at` menyimpan timestamp kapan data pajak pertama kali dibuat, dan `updated_at` menyimpan timestamp kapan data terakhir kali diupdate, diupdate otomatis setiap kali record dimodifikasi. Tabel ini tidak memiliki index tambahan karena relasi one-to-one dengan kendaraan sudah cukup untuk optimasi query.

Sistem akan otomatis menghitung `dp_pkb_saat_ini` setiap kali `njkb_saat_ini` atau `bobot_saat_ini` diubah, sehingga memastikan konsistensi data. Tabel ini menjadi referensi untuk menghitung pajak dalam setiap transaksi pembayaran pajak.

---

### 9. Tabel Transaksi Pajak

Tabel `transaksi_pajak` menyimpan riwayat pembayaran pajak kendaraan bermotor untuk setiap periode. Tabel ini merupakan tabel transaksional yang mencatat semua detail pembayaran pajak, termasuk pokok pajak, denda, tunggakan, dan berbagai komponen lainnya. Satu kendaraan dapat memiliki banyak transaksi untuk periode yang berbeda.

Field `id` merupakan primary key yang di-generate otomatis. Field `kendaraan` merupakan foreign key yang menghubungkan transaksi dengan kendaraan, menggunakan protect delete untuk mencegah penghapusan kendaraan yang masih memiliki transaksi.

Field `tahun` menyimpan tahun periode pajak dengan validasi minimum tahun 2000 dan memiliki index. Field `bulan` menyimpan bulan periode pajak dengan validasi antara 1 hingga 12 dan memiliki index. Field `tgl_pajak` menyimpan tanggal jatuh tempo pajak, bersifat opsional, dan memiliki index. Field `jml_tahun_bayar` menyimpan jumlah tahun yang dibayar dalam transaksi ini, default 1, dengan validasi minimum 0. Field `jml_bulan_bayar` menyimpan jumlah bulan yang dibayar dalam transaksi ini, default 0, dengan validasi minimum 0.

Field `tgl_bayar` menyimpan tanggal aktual pembayaran transaksi, bersifat opsional, dan memiliki index untuk analisis berdasarkan waktu pembayaran.

Komponen PKB (Pajak Kendaraan Bermotor) terdiri dari beberapa field. Field `pokok_pkb` menyimpan pokok PKB yang harus dibayar dengan presisi 15 digit dan 2 desimal. Field `denda_pkb` menyimpan denda PKB dengan presisi yang sama. Field `tunggakan_pokok_pkb` menyimpan tunggakan pokok PKB dari periode sebelumnya. Field `tunggakan_denda_pkb` menyimpan tunggakan denda PKB dari periode sebelumnya.

Komponen Opsen PKB terdiri dari field `opsen_pokok_pkb` yang menyimpan opsen dari pokok PKB, dan field `opsen_denda_pkb` yang menyimpan opsen dari denda PKB. Opsen merupakan bagian dari pendapatan yang dialokasikan untuk daerah.

Komponen SWDKLLJ (Sumbangan Wajib Dana Kecelakaan Lalu Lintas Jalan) terdiri dari field `pokok_swdkllj` untuk pokok SWDKLLJ, `denda_swdkllj` untuk denda SWDKLLJ, `tunggakan_pokok_swdkllj` untuk tunggakan pokok SWDKLLJ, dan `tunggakan_denda_swdkllj` untuk tunggakan denda SWDKLLJ.

Komponen BBNKB (Bea Balik Nama Kendaraan Bermotor) terdiri dari field `pokok_bbnkb` untuk pokok BBNKB, `denda_bbnkb` untuk denda BBNKB, dan `total_bbnkb` untuk total BBNKB yang dibayar. Komponen Opsen BBNKB terdiri dari field `opsen_pokok_bbnkb` untuk opsen pokok BBNKB, dan `opsen_denda_bbnkb` untuk opsen denda BBNKB.

Field `total_bayar` menyimpan total keseluruhan pembayaran yang dihitung otomatis dari semua komponen di atas, dengan presisi 15 digit dan 2 desimal, dan memiliki index untuk analisis pendapatan.

Field `created_at` menyimpan timestamp kapan transaksi pertama kali dibuat, dan `updated_at` menyimpan timestamp kapan transaksi terakhir kali diupdate. Tabel ini memiliki beberapa index untuk optimasi query, yaitu index pada kombinasi `tahun` dan `bulan`, `tgl_pajak`, `tgl_bayar`, kombinasi `kendaraan`, `tahun`, dan `bulan`, serta index pada `total_bayar`.

Sistem akan otomatis menghitung `total_bayar` setiap kali transaksi disimpan dengan menjumlahkan semua komponen pembayaran. Kombinasi `kendaraan`, `tahun`, dan `bulan` harus unik dalam sistem untuk mencegah duplikasi transaksi pada periode yang sama. Data diurutkan berdasarkan tahun dan bulan secara descending untuk menampilkan transaksi terbaru terlebih dahulu.

---

## 📈 Tabel Agregat dan Prediksi

Tabel-tabel agregat dan prediksi digunakan untuk analisis data dan peramalan pendapatan. Data dalam tabel-tabel ini dihasilkan dari proses agregasi dan perhitungan prediksi berdasarkan data transaksi.

---

### 10. Tabel Agregat Pendapatan Bulanan

Tabel `agregat_pendapatan_bulanan` menyimpan data agregasi pendapatan pajak kendaraan bermotor per bulan. Tabel ini berfungsi untuk mempercepat query analisis dan prediksi dengan melakukan pre-aggregation dari data transaksi. Data dalam tabel ini di-generate dari tabel `transaksi_pajak` dan dapat di-regenerate kapan saja untuk memastikan konsistensi.

Field `id` merupakan primary key yang di-generate otomatis. Field `jenis_kendaraan` merupakan foreign key yang menghubungkan agregat dengan jenis kendaraan tertentu, bersifat opsional (dapat null) untuk memungkinkan agregasi semua jenis kendaraan. Field `tahun` menyimpan tahun periode agregasi dengan index. Field `bulan` menyimpan bulan periode agregasi dengan index.

Field `total_pendapatan` menyimpan total keseluruhan pendapatan untuk periode tersebut dengan presisi 20 digit dan 2 desimal, default 0. Field `total_pokok_pkb` menyimpan total pokok PKB yang terkumpul dengan presisi yang sama. Field `total_denda_pkb` menyimpan total denda PKB yang terkumpul. Field `total_swdkllj` menyimpan total SWDKLLJ yang terkumpul. Field `total_bbnkb` menyimpan total BBNKB yang terkumpul. Field `total_opsen` menyimpan total opsen dari semua komponen yang terkumpul.

Field `jumlah_transaksi` menyimpan jumlah transaksi yang terjadi pada periode tersebut, default 0. Field `jumlah_kendaraan` menyimpan jumlah kendaraan unik yang melakukan transaksi pada periode tersebut, default 0.

Field `tanggal_agregasi` menyimpan timestamp kapan data agregat terakhir kali di-generate atau diupdate, diupdate otomatis setiap kali data di-regenerate.

Kombinasi `tahun`, `bulan`, dan `jenis_kendaraan` harus unik dalam sistem untuk mencegah duplikasi data agregat. Tabel ini memiliki index pada kombinasi `tahun` dan `bulan`, serta index pada `total_pendapatan` untuk mempercepat query analisis. Data diurutkan berdasarkan tahun dan bulan secara descending untuk menampilkan periode terbaru terlebih dahulu.

Tabel ini digunakan sebagai sumber data untuk proses prediksi pendapatan menggunakan metode Exponential Smoothing, sehingga sistem tidak perlu melakukan agregasi ulang setiap kali melakukan prediksi.

---

### 11. Tabel Hasil Prediksi

Tabel `hasil_prediksi` menyimpan hasil prediksi pendapatan pajak kendaraan bermotor yang dihasilkan dari perhitungan menggunakan metode Exponential Smoothing. Tabel ini mencatat semua detail prediksi termasuk metode yang digunakan, parameter model, hasil prediksi, dan metrik evaluasi akurasi.

Field `id` merupakan primary key yang di-generate otomatis. Field `jenis_kendaraan` merupakan foreign key yang menghubungkan prediksi dengan jenis kendaraan tertentu, bersifat opsional (dapat null) untuk memungkinkan prediksi semua jenis kendaraan. Field `tahun_prediksi` menyimpan tahun periode yang diprediksi dengan index. Field `bulan_prediksi` menyimpan bulan periode yang diprediksi dengan index, dengan validasi antara 1 hingga 12.

Field `metode` menyimpan metode prediksi yang digunakan dengan pilihan "SES" untuk Simple Exponential Smoothing, "DES" untuk Double Exponential Smoothing (Holt), dan "TES" untuk Triple Exponential Smoothing (Holt-Winters). Field `nilai_prediksi` menyimpan hasil prediksi pendapatan dengan presisi 20 digit dan 2 desimal.

Field `alpha` menyimpan parameter alpha yang digunakan dalam model dengan presisi 5 digit dan 4 desimal, bersifat opsional. Parameter alpha digunakan untuk smoothing level dalam semua metode. Field `beta` menyimpan parameter beta yang digunakan untuk smoothing trend dalam metode DES dan TES, dengan presisi yang sama, bersifat opsional. Field `gamma` menyimpan parameter gamma yang digunakan untuk smoothing seasonal dalam metode TES, dengan presisi yang sama, bersifat opsional. Field `seasonal_periods` menyimpan periode musiman yang digunakan dalam metode TES, default 12 untuk data bulanan, bersifat opsional.

Field `mape` menyimpan Mean Absolute Percentage Error yang mengukur akurasi prediksi dalam persen dengan presisi 10 digit dan 4 desimal, bersifat opsional. MAPE dihitung dengan membandingkan prediksi dengan data aktual historis. Field `mae` menyimpan Mean Absolute Error yang mengukur rata-rata selisih absolut antara prediksi dan aktual dengan presisi 20 digit dan 2 desimal, bersifat opsional. Field `rmse` menyimpan Root Mean Squared Error yang mengukur akurasi dengan memberikan bobot lebih pada error besar dengan presisi yang sama, bersifat opsional.

Field `nilai_aktual` menyimpan nilai pendapatan aktual setelah periode prediksi selesai, dengan presisi 20 digit dan 2 desimal, bersifat opsional. Field ini digunakan untuk evaluasi akurasi prediksi dengan membandingkan nilai prediksi dan aktual.

Field `tanggal_prediksi` menyimpan timestamp kapan prediksi dibuat, diisi otomatis saat record pertama kali disimpan. Field `data_training_dari` menyimpan tanggal mulai data historis yang digunakan untuk training model. Field `data_training_sampai` menyimpan tanggal akhir data historis yang digunakan untuk training model. Field `jumlah_data_training` menyimpan jumlah periode data historis yang digunakan untuk training model. Field `keterangan` menyimpan catatan tambahan tentang prediksi dalam bentuk text, bersifat opsional.

Tabel ini memiliki property `akurasi_persen` yang dihitung dari MAPE dengan formula 100 - MAPE, dan property `selisih` yang dihitung dari selisih antara nilai aktual dan nilai prediksi. Tabel ini memiliki index pada kombinasi `tahun_prediksi` dan `bulan_prediksi`, serta index pada `metode` untuk mempercepat query analisis. Data diurutkan berdasarkan tahun dan bulan prediksi secara descending untuk menampilkan prediksi terbaru terlebih dahulu.

Tabel ini digunakan untuk menyimpan hasil prediksi yang dapat dibandingkan dengan nilai aktual setelah periode prediksi selesai, sehingga sistem dapat mengevaluasi akurasi model dan melakukan perbaikan untuk prediksi selanjutnya.

---

## 🔗 Ringkasan Relasi Tabel

Sistem database ini memiliki struktur relasi yang terorganisir dengan baik. Tabel referensi (Kecamatan, Kelurahan, Jenis Kendaraan, Merek Kendaraan, Type Kendaraan) menjadi dasar untuk tabel data utama (Wajib Pajak, Kendaraan Bermotor, Data Pajak Kendaraan, Transaksi Pajak). Tabel agregat dan prediksi (Agregat Pendapatan Bulanan, Hasil Prediksi) menggunakan data dari tabel utama untuk analisis dan peramalan.

Alur data dimulai dari wajib pajak yang memiliki kendaraan bermotor, dimana setiap kendaraan memiliki data pajak terkini dan riwayat transaksi pembayaran pajak. Data transaksi kemudian diagregasi per bulan untuk mempercepat analisis, dan digunakan sebagai input untuk proses prediksi pendapatan menggunakan metode Exponential Smoothing. Hasil prediksi disimpan untuk evaluasi dan perbandingan dengan nilai aktual setelah periode prediksi selesai.

---

**Last Updated**: 2025-01-XX  
**Version**: 1.0
