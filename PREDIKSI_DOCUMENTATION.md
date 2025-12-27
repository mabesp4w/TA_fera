<!-- @format -->

# Dokumentasi Prediksi Pendapatan Pajak Kendaraan Bermotor

Dokumentasi lengkap untuk sistem prediksi pendapatan pajak kendaraan bermotor menggunakan metode Exponential Smoothing.

---

## 📋 Daftar Isi

1. [Pengenalan](#pengenalan)
2. [Metode Exponential Smoothing](#metode-exponential-smoothing)
   - [Simple Exponential Smoothing (SES)](#simple-exponential-smoothing-ses)
   - [Double Exponential Smoothing (DES)](#double-exponential-smoothing-des)
   - [Triple Exponential Smoothing (TES)](#triple-exponential-smoothing-tes)
3. [Persiapan Data](#persiapan-data)
4. [API Endpoints](#api-endpoints)
   - [Generate Prediksi](#1-generate-prediksi)
   - [Compare Methods](#2-compare-methods)
   - [Chart Data](#3-chart-data)
   - [Evaluation](#4-evaluation)
   - [Trend Data](#5-trend-data)
5. [Contoh Penggunaan](#contoh-penggunaan)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Pengenalan

Sistem prediksi ini menggunakan tiga metode Exponential Smoothing untuk memprediksi pendapatan pajak kendaraan bermotor di UPPD/SAMSAT Jayapura:

- **Simple Exponential Smoothing (SES)**: Untuk data tanpa trend dan seasonality
- **Double Exponential Smoothing (DES/Holt)**: Untuk data dengan trend
- **Triple Exponential Smoothing (TES/Holt-Winters)**: Untuk data dengan trend dan seasonality

Sistem ini menggunakan data historis dari `AgregatPendapatanBulanan` untuk melakukan prediksi dan menyimpan hasilnya di `HasilPrediksi`.

---

## 📊 Metode Exponential Smoothing

### Simple Exponential Smoothing (SES)

**Kapan digunakan:**
- Data tidak memiliki trend (naik/turun)
- Data tidak memiliki pola musiman
- Data relatif stabil dari waktu ke waktu

**Parameter:**
- `alpha` (α): Parameter smoothing level (0-1)
  - Nilai kecil (0.1-0.3): Lebih smooth, responsif lambat
  - Nilai besar (0.7-0.9): Lebih responsif, kurang smooth

**Formula:**
```
F(t+1) = α × Y(t) + (1-α) × F(t)
```

**Contoh:**
```json
{
  "metode": "SES",
  "tahun_prediksi": 2025,
  "bulan_prediksi": 1,
  "alpha": 0.3,
  "optimize": true
}
```

### Double Exponential Smoothing (DES)

**Kapan digunakan:**
- Data memiliki trend (naik atau turun)
- Data tidak memiliki pola musiman
- Trend relatif konstan

**Parameter:**
- `alpha` (α): Parameter smoothing level (0-1)
- `beta` (β): Parameter smoothing trend (0-1)
  - Beta kecil: Trend lebih stabil
  - Beta besar: Trend lebih responsif

**Formula:**
```
Level: L(t) = α × Y(t) + (1-α) × (L(t-1) + T(t-1))
Trend: T(t) = β × (L(t) - L(t-1)) + (1-β) × T(t-1)
Prediksi: F(t+1) = L(t) + T(t)
```

**Contoh:**
```json
{
  "metode": "DES",
  "tahun_prediksi": 2025,
  "bulan_prediksi": 1,
  "alpha": 0.3,
  "beta": 0.2,
  "optimize": true
}
```

### Triple Exponential Smoothing (TES)

**Kapan digunakan:**
- Data memiliki trend
- Data memiliki pola musiman (seasonal pattern)
- Data bulanan dengan pola tahunan (12 bulan)

**Parameter:**
- `alpha` (α): Parameter smoothing level (0-1)
- `beta` (β): Parameter smoothing trend (0-1)
- `gamma` (γ): Parameter smoothing seasonal (0-1)
- `seasonal_periods`: Periode musiman (default: 12 untuk data bulanan)

**Formula:**
```
Level: L(t) = α × (Y(t) / S(t-s)) + (1-α) × (L(t-1) + T(t-1))
Trend: T(t) = β × (L(t) - L(t-1)) + (1-β) × T(t-1)
Seasonal: S(t) = γ × (Y(t) / L(t)) + (1-γ) × S(t-s)
Prediksi: F(t+h) = (L(t) + h × T(t)) × S(t-s+h)
```

**Contoh:**
```json
{
  "metode": "TES",
  "tahun_prediksi": 2025,
  "bulan_prediksi": 1,
  "seasonal_periods": 12,
  "alpha": 0.3,
  "beta": 0.2,
  "gamma": 0.1,
  "optimize": true
}
```

---

## 📥 Persiapan Data

Sebelum melakukan prediksi, pastikan data historis sudah tersedia:

### 1. Regenerate Agregat Pendapatan Bulanan

Data prediksi menggunakan `AgregatPendapatanBulanan` sebagai input. Pastikan data ini sudah terisi:

```bash
# Regenerate semua data
POST /crud/agregat-pendapatan-bulanan/regenerate/?all=true

# Regenerate untuk tahun tertentu
POST /crud/agregat-pendapatan-bulanan/regenerate/?tahun=2024

# Regenerate untuk jenis kendaraan tertentu
POST /crud/agregat-pendapatan-bulanan/regenerate/?jenis_kendaraan_id=1
```

### 2. Minimum Data yang Diperlukan

- **SES**: Minimal 2 periode data
- **DES**: Minimal 3 periode data
- **TES**: Minimal 24 periode data (2 × seasonal_periods)

### 3. Verifikasi Data

```bash
# Cek data agregat yang tersedia
GET /crud/agregat-pendapatan-bulanan/?page_size=100
```

---

## 🔌 API Endpoints

### 1. Generate Prediksi

Generate prediksi baru menggunakan salah satu metode (SES, DES, atau TES).

**Endpoint:**
```http
POST /crud/prediksi/generate/
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "metode": "SES",  // Required: "SES", "DES", atau "TES"
  "jenis_kendaraan_id": 1,  // Optional: Filter by jenis kendaraan
  "tahun_prediksi": 2025,  // Required
  "bulan_prediksi": 1,  // Required (1-12)
  "alpha": 0.3,  // Optional: Parameter alpha (0-1)
  "beta": 0.2,  // Optional: Parameter beta (untuk DES/TES)
  "gamma": 0.1,  // Optional: Parameter gamma (untuk TES)
  "seasonal_periods": 12,  // Optional: Untuk TES (default: 12)
  "optimize": true,  // Optional: Auto-optimize parameter (default: true)
  "keterangan": "Prediksi untuk bulan Januari 2025"  // Optional
}
```

**Response Success:**
```json
{
  "status": "success",
  "message": "Prediksi menggunakan SES berhasil dibuat",
  "results": {
    "id": 1,
    "jenis_kendaraan": 1,
    "jenis_kendaraan_nama": "Honda Beat",
    "jenis_kendaraan_kategori": "MOTOR",
    "tahun_prediksi": 2025,
    "bulan_prediksi": 1,
    "metode": "SES",
    "metode_display": "Simple Exponential Smoothing",
    "nilai_prediksi": "50000000.00",
    "alpha": "0.35",
    "beta": null,
    "gamma": null,
    "mape": "5.25",
    "mae": "2500000.00",
    "rmse": "3000000.00",
    "nilai_aktual": null,
    "akurasi_persen": 94.75,
    "selisih": null,
    "data_training_dari": "2023-01-01",
    "data_training_sampai": "2024-12-31",
    "jumlah_data_training": 24,
    "tanggal_prediksi": "2025-01-01T00:00:00Z"
  }
}
```

**Contoh Penggunaan:**

```bash
# Generate prediksi dengan SES (auto-optimize)
curl -X POST http://localhost:8000/crud/prediksi/generate/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "metode": "SES",
    "tahun_prediksi": 2025,
    "bulan_prediksi": 1
  }'

# Generate prediksi dengan DES (manual parameter)
curl -X POST http://localhost:8000/crud/prediksi/generate/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "metode": "DES",
    "tahun_prediksi": 2025,
    "bulan_prediksi": 1,
    "alpha": 0.3,
    "beta": 0.2,
    "optimize": false
  }'

# Generate prediksi dengan TES untuk jenis kendaraan tertentu
curl -X POST http://localhost:8000/crud/prediksi/generate/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "metode": "TES",
    "jenis_kendaraan_id": 1,
    "tahun_prediksi": 2025,
    "bulan_prediksi": 1,
    "seasonal_periods": 12
  }'
```

---

### 2. Compare Methods

Bandingkan ketiga metode (SES, DES, TES) sekaligus dan dapatkan rekomendasi metode terbaik.

**Endpoint:**
```http
POST /crud/prediksi/compare/
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "jenis_kendaraan_id": 1,  // Optional
  "tahun_prediksi": 2025,  // Required
  "bulan_prediksi": 1  // Required
}
```

**Response Success:**
```json
{
  "status": "success",
  "message": "Perbandingan metode prediksi berhasil dibuat",
  "results": {
    "results": {
      "SES": {
        "nilai_prediksi": 50000000.00,
        "alpha": 0.35,
        "mape": 5.25,
        "mae": 2500000.00,
        "rmse": 3000000.00,
        "jumlah_data_training": 24
      },
      "DES": {
        "nilai_prediksi": 52000000.00,
        "alpha": 0.30,
        "beta": 0.20,
        "mape": 4.80,
        "mae": 2300000.00,
        "rmse": 2800000.00,
        "jumlah_data_training": 24
      },
      "TES": {
        "nilai_prediksi": 51000000.00,
        "alpha": 0.25,
        "beta": 0.15,
        "gamma": 0.10,
        "mape": 4.50,
        "mae": 2200000.00,
        "rmse": 2700000.00,
        "jumlah_data_training": 24
      }
    },
    "best_method": "TES",
    "best_mape": 4.50,
    "recommendation": "Metode terbaik: TES dengan MAPE 4.50%"
  }
}
```

**Contoh Penggunaan:**

```bash
# Bandingkan semua metode
curl -X POST http://localhost:8000/crud/prediksi/compare/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "tahun_prediksi": 2025,
    "bulan_prediksi": 1
  }'
```

---

### 3. Chart Data

Ambil data untuk visualisasi chart (aktual vs prediksi).

**Endpoint:**
```http
GET /crud/prediksi/chart/
Authorization: Bearer <token>
```

**Query Parameters:**
- `jenis_kendaraan_id` (optional): Filter by jenis kendaraan
- `tahun` (optional): Filter by tahun
- `metode` (optional): Filter by metode (SES, DES, TES)
- `limit` (optional): Jumlah data terakhir (default: 24)

**Response Success:**
```json
{
  "status": "success",
  "message": "Data chart berhasil diambil",
  "results": {
    "labels": [
      "2023-01", "2023-02", "2023-03", ...,
      "2024-12", "2025-01"
    ],
    "aktual": [
      45000000, 46000000, 47000000, ...,
      49000000, null
    ],
    "prediksi": {
      "SES": [
        null, null, null, ...,
        null, 50000000
      ],
      "DES": [
        null, null, null, ...,
        null, 52000000
      ],
      "TES": [
        null, null, null, ...,
        null, 51000000
      ]
    }
  }
}
```

**Contoh Penggunaan:**

```bash
# Ambil data chart untuk 24 bulan terakhir
curl -X GET "http://localhost:8000/crud/prediksi/chart/?limit=24" \
  -H "Authorization: Bearer <token>"

# Ambil data chart untuk jenis kendaraan tertentu
curl -X GET "http://localhost:8000/crud/prediksi/chart/?jenis_kendaraan_id=1&limit=36" \
  -H "Authorization: Bearer <token>"

# Ambil data chart untuk tahun tertentu
curl -X GET "http://localhost:8000/crud/prediksi/chart/?tahun=2024&metode=TES" \
  -H "Authorization: Bearer <token>"
```

---

### 4. Evaluation

Evaluasi akurasi model berdasarkan prediksi yang sudah memiliki nilai aktual.

**Endpoint:**
```http
GET /crud/prediksi/evaluation/
Authorization: Bearer <token>
```

**Query Parameters:**
- `jenis_kendaraan_id` (optional): Filter by jenis kendaraan
- `metode` (optional): Filter by metode
- `tahun` (optional): Filter by tahun

**Response Success:**
```json
{
  "status": "success",
  "message": "Evaluasi akurasi model berhasil diambil",
  "results": {
    "evaluation": {
      "SES": {
        "total": 12,
        "avg_mape": 5.25,
        "avg_mae": 2500000.00,
        "avg_rmse": 3000000.00,
        "avg_akurasi": 94.75,
        "predictions": [
          {
            "id": 1,
            "tahun": 2024,
            "bulan": 1,
            "prediksi": 50000000.00,
            "aktual": 52000000.00,
            "mape": 3.85,
            "mae": 2000000.00,
            "rmse": 2000000.00,
            "akurasi_persen": 96.15,
            "selisih": 2000000.00
          },
          ...
        ]
      },
      "DES": {
        "total": 12,
        "avg_mape": 4.80,
        "avg_mae": 2300000.00,
        "avg_rmse": 2800000.00,
        "avg_akurasi": 95.20,
        "predictions": [...]
      },
      "TES": {
        "total": 12,
        "avg_mape": 4.50,
        "avg_mae": 2200000.00,
        "avg_rmse": 2700000.00,
        "avg_akurasi": 95.50,
        "predictions": [...]
      }
    },
    "best_method": "TES",
    "best_avg_mape": 4.50,
    "summary": {
      "total_predictions_evaluated": 36,
      "methods_tested": ["SES", "DES", "TES"]
    }
  }
}
```

**Contoh Penggunaan:**

```bash
# Evaluasi semua metode
curl -X GET "http://localhost:8000/crud/prediksi/evaluation/" \
  -H "Authorization: Bearer <token>"

# Evaluasi untuk metode tertentu
curl -X GET "http://localhost:8000/crud/prediksi/evaluation/?metode=TES" \
  -H "Authorization: Bearer <token>"

# Evaluasi untuk jenis kendaraan tertentu
curl -X GET "http://localhost:8000/crud/prediksi/evaluation/?jenis_kendaraan_id=1" \
  -H "Authorization: Bearer <token>"
```

---

### 5. Trend Data

Ambil data trend pendapatan historis dengan statistik.

**Endpoint:**
```http
GET /crud/prediksi/trend/
Authorization: Bearer <token>
```

**Query Parameters:**
- `jenis_kendaraan_id` (optional): Filter by jenis kendaraan
- `start_year` (optional): Tahun mulai
- `end_year` (optional): Tahun akhir
- `limit` (optional): Jumlah data terakhir

**Response Success:**
```json
{
  "status": "success",
  "message": "Data trend pendapatan berhasil diambil",
  "results": {
    "data": [
      {
        "tahun": 2023,
        "bulan": 1,
        "total_pendapatan": 45000000.00,
        "jenis_kendaraan_id": 1
      },
      ...
    ],
    "statistics": {
      "min": 40000000.00,
      "max": 55000000.00,
      "mean": 47500000.00,
      "median": 47000000.00,
      "std": 5000000.00,
      "total_periods": 24
    },
    "trend": "increasing"
  }
}
```

**Contoh Penggunaan:**

```bash
# Ambil trend data
curl -X GET "http://localhost:8000/crud/prediksi/trend/?limit=36" \
  -H "Authorization: Bearer <token>"

# Ambil trend untuk rentang tahun tertentu
curl -X GET "http://localhost:8000/crud/prediksi/trend/?start_year=2023&end_year=2024" \
  -H "Authorization: Bearer <token>"
```

---

## 📝 Contoh Penggunaan

### Workflow Lengkap: Prediksi Pendapatan Bulan Depan

#### Langkah 1: Regenerate Data Agregat

```bash
# Regenerate semua data agregat dari TransaksiPajak
POST /crud/agregat-pendapatan-bulanan/regenerate/?all=true
```

#### Langkah 2: Bandingkan Metode

```bash
# Bandingkan ketiga metode untuk menentukan yang terbaik
POST /crud/prediksi/compare/
{
  "tahun_prediksi": 2025,
  "bulan_prediksi": 1
}
```

**Hasil:** Sistem akan merekomendasikan metode terbaik berdasarkan MAPE terendah.

#### Langkah 3: Generate Prediksi dengan Metode Terbaik

```bash
# Generate prediksi menggunakan metode terbaik (misalnya TES)
POST /crud/prediksi/generate/
{
  "metode": "TES",
  "tahun_prediksi": 2025,
  "bulan_prediksi": 1,
  "keterangan": "Prediksi untuk bulan Januari 2025 menggunakan TES"
}
```

#### Langkah 4: Visualisasi Hasil

```bash
# Ambil data untuk chart
GET /crud/prediksi/chart/?limit=24
```

#### Langkah 5: Update Nilai Aktual (Setelah Periode Selesai)

Setelah periode prediksi selesai dan data aktual tersedia:

```bash
# Update nilai aktual untuk evaluasi
PATCH /crud/hasil-prediksi/<id>/
{
  "nilai_aktual": 52000000.00
}
```

#### Langkah 6: Evaluasi Akurasi

```bash
# Evaluasi akurasi model
GET /crud/prediksi/evaluation/
```

---

### Skenario 2: Prediksi untuk Jenis Kendaraan Tertentu

```bash
# 1. Regenerate agregat untuk jenis kendaraan tertentu
POST /crud/agregat-pendapatan-bulanan/regenerate/?jenis_kendaraan_id=1

# 2. Bandingkan metode untuk jenis kendaraan tersebut
POST /crud/prediksi/compare/
{
  "jenis_kendaraan_id": 1,
  "tahun_prediksi": 2025,
  "bulan_prediksi": 1
}

# 3. Generate prediksi
POST /crud/prediksi/generate/
{
  "metode": "TES",
  "jenis_kendaraan_id": 1,
  "tahun_prediksi": 2025,
  "bulan_prediksi": 1
}
```

---

### Skenario 3: Batch Prediction (Prediksi Beberapa Bulan)

```bash
# Generate prediksi untuk 12 bulan ke depan
for bulan in {1..12}; do
  POST /crud/prediksi/generate/
  {
    "metode": "TES",
    "tahun_prediksi": 2025,
    "bulan_prediksi": $bulan
  }
done
```

---

## ✅ Best Practices

### 1. Persiapan Data

- ✅ **Regenerate agregat secara berkala**: Setelah ada transaksi baru, regenerate agregat
- ✅ **Pastikan data cukup**: Minimal 24 periode untuk hasil yang baik
- ✅ **Validasi data**: Pastikan tidak ada data anomali atau outlier yang signifikan

### 2. Pemilihan Metode

- ✅ **Gunakan Compare Methods**: Selalu bandingkan ketiga metode sebelum generate prediksi
- ✅ **Pilih berdasarkan MAPE**: Metode dengan MAPE terendah biasanya lebih akurat
- ✅ **Pertimbangkan karakteristik data**:
  - Data stabil tanpa trend → SES
  - Data dengan trend → DES
  - Data dengan trend dan seasonality → TES

### 3. Optimasi Parameter

- ✅ **Gunakan auto-optimize**: Biarkan sistem mencari parameter optimal (default: `optimize: true`)
- ✅ **Manual tuning**: Jika hasil tidak memuaskan, coba parameter manual
- ✅ **Validasi dengan data testing**: Gunakan data historis untuk validasi

### 4. Evaluasi Model

- ✅ **Update nilai aktual**: Setelah periode prediksi selesai, update `nilai_aktual`
- ✅ **Monitor akurasi**: Evaluasi akurasi secara berkala
- ✅ **Perbandingan metode**: Bandingkan performa metode secara berkala

### 5. Visualisasi

- ✅ **Gunakan chart data**: Visualisasikan aktual vs prediksi untuk analisis
- ✅ **Monitor trend**: Gunakan trend data untuk memahami pola
- ✅ **Perbandingan visual**: Bandingkan prediksi dari berbagai metode

---

## 🔧 Troubleshooting

### Error: "Data historis tidak cukup"

**Penyebab**: Data `AgregatPendapatanBulanan` kurang dari minimum yang diperlukan.

**Solusi**:
```bash
# 1. Regenerate agregat dari TransaksiPajak
POST /crud/agregat-pendapatan-bulanan/regenerate/?all=true

# 2. Verifikasi jumlah data
GET /crud/agregat-pendapatan-bulanan/?page_size=100

# 3. Pastikan minimal:
#    - SES: 2 periode
#    - DES: 3 periode
#    - TES: 24 periode
```

### Error: "Optimization failed"

**Penyebab**: Gagal optimasi parameter karena data tidak valid atau terlalu sedikit.

**Solusi**:
```bash
# 1. Gunakan parameter manual
POST /crud/prediksi/generate/
{
  "metode": "SES",
  "alpha": 0.3,
  "optimize": false
}

# 2. Atau coba metode lain yang memerlukan data lebih sedikit (SES atau DES)
```

### Prediksi Tidak Akurat

**Penyebab**: 
- Data historis tidak cukup
- Parameter tidak optimal
- Metode tidak sesuai dengan karakteristik data

**Solusi**:
```bash
# 1. Bandingkan semua metode
POST /crud/prediksi/compare/
{
  "tahun_prediksi": 2025,
  "bulan_prediksi": 1
}

# 2. Gunakan metode dengan MAPE terendah

# 3. Pastikan data historis cukup (minimal 24 periode)

# 4. Regenerate agregat dengan data terbaru
POST /crud/agregat-pendapatan-bulanan/regenerate/?all=true
```

### Error: "Jenis kendaraan tidak ditemukan"

**Penyebab**: ID jenis kendaraan tidak valid.

**Solusi**:
```bash
# 1. Cek jenis kendaraan yang tersedia
GET /crud/jenis-kendaraan/

# 2. Gunakan ID yang valid atau tidak perlu filter (None = semua)
```

### MAPE Sangat Tinggi (>20%)

**Penyebab**: 
- Data memiliki variasi tinggi
- Outlier dalam data
- Metode tidak sesuai

**Solusi**:
```bash
# 1. Cek trend data untuk identifikasi outlier
GET /crud/prediksi/trend/

# 2. Coba metode lain (TES biasanya lebih akurat untuk data dengan seasonality)

# 3. Filter by jenis kendaraan untuk data yang lebih homogen

# 4. Gunakan data training yang lebih panjang
```

---

## 📈 Interpretasi Hasil

### Metrik Evaluasi

#### MAPE (Mean Absolute Percentage Error)
- **< 5%**: Sangat baik
- **5-10%**: Baik
- **10-20%**: Cukup
- **> 20%**: Perlu perbaikan

#### MAE (Mean Absolute Error)
- Menunjukkan rata-rata selisih absolut antara prediksi dan aktual
- Semakin kecil semakin baik
- Satuan sama dengan data (Rupiah)

#### RMSE (Root Mean Squared Error)
- Menunjukkan akurasi dengan memberikan bobot lebih pada error besar
- Semakin kecil semakin baik
- Lebih sensitif terhadap outlier dibanding MAE

### Akurasi Persen
- Dihitung dari MAPE: `Akurasi = 100 - MAPE`
- **> 95%**: Sangat baik
- **90-95%**: Baik
- **80-90%**: Cukup
- **< 80%**: Perlu perbaikan

---

## 🔄 Workflow Rekomendasi

### Untuk Prediksi Bulanan Rutin

1. **Setiap akhir bulan**:
   ```bash
   # Regenerate agregat dengan data bulan terakhir
   POST /crud/agregat-pendapatan-bulanan/regenerate/
   ```

2. **Awal bulan berikutnya**:
   ```bash
   # Bandingkan metode
   POST /crud/prediksi/compare/
   
   # Generate prediksi dengan metode terbaik
   POST /crud/prediksi/generate/
   ```

3. **Setelah periode selesai**:
   ```bash
   # Update nilai aktual
   PATCH /crud/hasil-prediksi/<id>/
   
   # Evaluasi akurasi
   GET /crud/prediksi/evaluation/
   ```

---

## 📚 Referensi

- **Exponential Smoothing**: Metode peramalan time series yang memberikan bobot eksponensial pada observasi terbaru
- **Simple Exponential Smoothing**: Cocok untuk data tanpa trend dan seasonality
- **Holt's Method (DES)**: Ekstensi SES untuk data dengan trend
- **Holt-Winters Method (TES)**: Ekstensi DES untuk data dengan trend dan seasonality

---

## 📞 Bantuan

Jika mengalami masalah:

1. Cek dokumentasi troubleshooting di atas
2. Verifikasi data historis cukup
3. Coba metode lain atau parameter manual
4. Pastikan agregat pendapatan sudah di-regenerate
5. Cek log error untuk detail lebih lanjut

---

**Last Updated**: 2025-01-XX  
**Version**: 1.0

