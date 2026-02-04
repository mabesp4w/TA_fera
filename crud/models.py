from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()

# ============================================
# REFERENCE TABLES (Yang Benar-Benar Perlu)
# ============================================

class Kecamatan(models.Model):
    """Data kecamatan"""
    # Fields
    nama = models.CharField(max_length=100, unique=True, db_index=True)
    
    class Meta:
        db_table = 'kecamatan'
        verbose_name = 'Kecamatan'
        verbose_name_plural = 'Kecamatan'
        ordering = ['nama']
    
    def __str__(self):
        return self.nama


class Kelurahan(models.Model):
    """Data kelurahan/desa"""
    # ForeignKey
    kecamatan = models.ForeignKey(Kecamatan, on_delete=models.CASCADE, related_name='kelurahan')
    
    # Fields
    nama = models.CharField(max_length=100, db_index=True)
    
    class Meta:
        db_table = 'kelurahan'
        verbose_name = 'Kelurahan'
        verbose_name_plural = 'Kelurahan'
        ordering = ['nama']
        unique_together = ['kecamatan', 'nama']
    
    def __str__(self):
        return f"{self.nama}, {self.kecamatan.nama}"


class JenisKendaraan(models.Model):
    """Data jenis kendaraan"""
    nama = models.CharField(max_length=100, unique=True, db_index=True)
    kategori = models.CharField(
        max_length=50,
        choices=[
            ('MOTOR', 'Sepeda Motor'),
            ('MOBIL', 'Mobil'),
            ('JEEP', 'Jeep'),
            ('TRUK', 'Truk'),
            ('BUS', 'Bus'),
            ('LAINNYA', 'Lainnya')
        ],
        default='MOTOR'
    )
    
    class Meta:
        db_table = 'jenis_kendaraan'
        verbose_name = 'Jenis Kendaraan'
        verbose_name_plural = 'Jenis Kendaraan'
        ordering = ['nama']
    
    def __str__(self):
        return self.nama


class MerekKendaraan(models.Model):
    """Data merek kendaraan"""
    nama = models.CharField(max_length=100, unique=True, db_index=True)
    
    class Meta:
        db_table = 'merek_kendaraan'
        verbose_name = 'Merek Kendaraan'
        verbose_name_plural = 'Merek Kendaraan'
        ordering = ['nama']
    
    def __str__(self):
        return self.nama


class TypeKendaraan(models.Model):
    """Data type kendaraan"""
    # ForeignKey
    merek = models.ForeignKey(MerekKendaraan, on_delete=models.CASCADE, related_name='type_kendaraan')
    
    # Fields
    nama = models.CharField(max_length=200, db_index=True)
    
    class Meta:
        db_table = 'type_kendaraan'
        verbose_name = 'Type Kendaraan'
        verbose_name_plural = 'Type Kendaraan'
        ordering = ['merek', 'nama']
        unique_together = ['merek', 'nama']
    
    def __str__(self):
        return f"{self.merek.nama} - {self.nama}"


# ============================================
# MAIN DATA TABLES
# ============================================

class WajibPajak(models.Model):
    """Data wajib pajak/pemilik kendaraan"""
    
    # ForeignKey
    kelurahan = models.ForeignKey(Kelurahan, on_delete=models.PROTECT, related_name='wajib_pajak', null=True, blank=True)
    
    # Fields
    no_ktp = models.CharField(max_length=50, db_index=True, blank=True, null=True)
    nama = models.CharField(max_length=200, db_index=True)
    
    # Alamat
    alamat = models.TextField()
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'wajib_pajak'
        verbose_name = 'Wajib Pajak'
        verbose_name_plural = 'Wajib Pajak'
        indexes = [
            models.Index(fields=['no_ktp']),
            models.Index(fields=['nama']),
        ]
    
    def __str__(self):
        return self.nama


class KendaraanBermotor(models.Model):
    """Data kendaraan bermotor"""
    
    # ForeignKey
    jenis = models.ForeignKey(JenisKendaraan, on_delete=models.PROTECT, related_name='kendaraan')
    type_kendaraan = models.ForeignKey(TypeKendaraan, on_delete=models.PROTECT, related_name='kendaraan')
    wajib_pajak = models.ForeignKey(WajibPajak, on_delete=models.PROTECT, related_name='kendaraan')
    
    # Choices untuk field yang sederhana
    WARNA_CHOICES = [
        ('HITAM', 'Hitam'),
        ('PUTIH', 'Putih'),
        ('MERAH', 'Merah'),
        ('ABU-ABU', 'Abu-abu'),
        ('SILVER', 'Silver'),
        ('BIRU', 'Biru'),
        ('HIJAU', 'Hijau'),
        ('KUNING', 'Kuning'),
    ]
    
    BBM_CHOICES = [
        ('BENSIN', 'Bensin'),
        ('SOLAR', 'Solar'),
        ('LISTRIK', 'Listrik'),
        ('HYBRID', 'Hybrid'),
    ]
    
    # Identitas Kendaraan
    no_polisi = models.CharField(max_length=20, unique=True, db_index=True)
    no_rangka = models.CharField(max_length=50, unique=True, db_index=True)
    no_mesin = models.CharField(max_length=100, db_index=True)
    
    # Spesifikasi Kendaraan
    tahun_buat = models.IntegerField(validators=[MinValueValidator(1900), MaxValueValidator(2100)], db_index=True)
    jml_cc = models.IntegerField(verbose_name="Kapasitas Mesin (CC)")
    bbm = models.CharField(max_length=50, choices=BBM_CHOICES)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'kendaraan_bermotor'
        verbose_name = 'Kendaraan Bermotor'
        verbose_name_plural = 'Kendaraan Bermotor'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['no_polisi']),
            models.Index(fields=['no_rangka']),
            models.Index(fields=['wajib_pajak', 'tahun_buat']),
            models.Index(fields=['jenis', 'type_kendaraan']),
            models.Index(fields=['tahun_buat']),
        ]
    
    def __str__(self):
        return f"{self.no_polisi} - {self.type_kendaraan.merek.nama} {self.type_kendaraan.nama}"
    
    @property
    def njkb_saat_ini(self):
        """Helper property untuk backward compatibility"""
        return self.data_pajak.njkb_saat_ini if hasattr(self, 'data_pajak') and self.data_pajak else 0
    
    @property
    def dp_pkb_saat_ini(self):
        """Helper property untuk backward compatibility"""
        return self.data_pajak.dp_pkb_saat_ini if hasattr(self, 'data_pajak') and self.data_pajak else 0
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Auto calculate DP PKB di DataPajakKendaraan jika ada
        if hasattr(self, 'data_pajak') and self.data_pajak:
            if self.data_pajak.njkb_saat_ini and self.data_pajak.bobot_saat_ini:
                self.data_pajak.dp_pkb_saat_ini = self.data_pajak.njkb_saat_ini * self.data_pajak.bobot_saat_ini
                self.data_pajak.save()


class DataPajakKendaraan(models.Model):
    """Data pajak kendaraan saat ini (dapat berubah setiap transaksi)"""
    # ForeignKey (OneToOne)
    kendaraan = models.OneToOneField(KendaraanBermotor, on_delete=models.CASCADE, related_name='data_pajak')
    
    # NJKB dan Pajak
    njkb_saat_ini = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="NJKB Saat Ini")
    bobot_saat_ini = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    dp_pkb_saat_ini = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Dasar Pengenaan PKB")
    tarif_pkb_saat_ini = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Tarif PKB dalam persen")
    
    # Metadata
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'data_pajak_kendaraan'
        verbose_name = 'Data Pajak Kendaraan'
        verbose_name_plural = 'Data Pajak Kendaraan'
    
    def __str__(self):
        return f"{self.kendaraan.no_polisi} - NJKB: Rp {self.njkb_saat_ini:,.0f}"
    
    def save(self, *args, **kwargs):
        # Auto calculate DP PKB
        if self.njkb_saat_ini and self.bobot_saat_ini:
            self.dp_pkb_saat_ini = self.njkb_saat_ini * self.bobot_saat_ini
        super().save(*args, **kwargs)


class TransaksiPajak(models.Model):
    """Data transaksi pembayaran pajak kendaraan"""
    
    # ForeignKey
    kendaraan = models.ForeignKey(KendaraanBermotor, on_delete=models.PROTECT, related_name='transaksi')
    
    # Periode Pajak
    tahun = models.IntegerField(validators=[MinValueValidator(2000)], db_index=True)
    bulan = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)], db_index=True)
    tgl_pajak = models.DateField(db_index=True, null=True, blank=True)
    
    # Periode Pembayaran
    jml_tahun_bayar = models.IntegerField(default=1, validators=[MinValueValidator(0)])
    jml_bulan_bayar = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    # === TRANSAKSI AKTUAL ===
    # Tanggal Transaksi
    tgl_bayar = models.DateField(blank=True, null=True, db_index=True)
    
    # === PKB (Pajak Kendaraan Bermotor) ===
    pokok_pkb = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    denda_pkb = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tunggakan_pokok_pkb = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tunggakan_denda_pkb = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # === OPSEN PKB ===
    opsen_pokok_pkb = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    opsen_denda_pkb = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # === SWDKLLJ ===
    pokok_swdkllj = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    denda_swdkllj = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tunggakan_pokok_swdkllj = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tunggakan_denda_swdkllj = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # === BBNKB (Bea Balik Nama Kendaraan Bermotor) ===
    pokok_bbnkb = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    denda_bbnkb = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_bbnkb = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # === OPSEN BBNKB ===
    opsen_pokok_bbnkb = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    opsen_denda_bbnkb = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # === TOTAL ===
    total_bayar = models.DecimalField(max_digits=15, decimal_places=2, default=0, db_index=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'transaksi_pajak'
        verbose_name = 'Transaksi Pajak'
        verbose_name_plural = 'Transaksi Pajak'
        ordering = ['-tahun', '-bulan']
        indexes = [
            models.Index(fields=['tahun', 'bulan']),
            models.Index(fields=['tgl_pajak']),
            models.Index(fields=['tgl_bayar']),
            models.Index(fields=['kendaraan', 'tahun', 'bulan']),
            models.Index(fields=['total_bayar']),
        ]
    
    def __str__(self):
        return f"{self.kendaraan.no_polisi} - {self.tahun}-{self.bulan:02d} - Rp {self.total_bayar:,.0f}"
    
    def save(self, *args, **kwargs):
        # Auto calculate total bayar
        self.total_bayar = (
            self.pokok_pkb +
            self.denda_pkb +
            self.tunggakan_pokok_pkb +
            self.tunggakan_denda_pkb +
            self.opsen_pokok_pkb +
            self.opsen_denda_pkb +
            self.pokok_swdkllj +
            self.denda_swdkllj +
            self.tunggakan_pokok_swdkllj +
            self.tunggakan_denda_swdkllj +
            self.pokok_bbnkb +
            self.denda_bbnkb +
            self.opsen_pokok_bbnkb +
            self.opsen_denda_bbnkb
        )
        super().save(*args, **kwargs)


# ============================================
# AGREGAT & PREDIKSI
# ============================================

class AgregatPendapatanBulanan(models.Model):
    """Agregasi pendapatan per bulan (untuk mempercepat query prediksi)"""
    
    # ForeignKey
    jenis_kendaraan = models.ForeignKey(JenisKendaraan, on_delete=models.CASCADE, blank=True, null=True)
    
    # Periode
    tahun = models.IntegerField(db_index=True)
    bulan = models.IntegerField(db_index=True)
    
    # Total Pendapatan
    total_pendapatan = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    total_pokok_pkb = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    total_denda_pkb = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    total_swdkllj = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    total_bbnkb = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    total_opsen = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    
    # Jumlah Transaksi
    jumlah_transaksi = models.IntegerField(default=0)
    jumlah_kendaraan = models.IntegerField(default=0)
    
    # Metadata
    tanggal_agregasi = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'agregat_pendapatan_bulanan'
        verbose_name = 'Agregat Pendapatan Bulanan'
        verbose_name_plural = 'Agregat Pendapatan Bulanan'
        unique_together = ['tahun', 'bulan', 'jenis_kendaraan']
        ordering = ['-tahun', '-bulan']
        indexes = [
            models.Index(fields=['tahun', 'bulan']),
            models.Index(fields=['total_pendapatan']),
        ]
    
    def __str__(self):
        return f"{self.tahun}-{self.bulan:02d} - Rp {self.total_pendapatan:,.0f}"


class HasilPrediksi(models.Model):
    """Model untuk menyimpan hasil prediksi"""
    
    # ForeignKey
    jenis_kendaraan = models.ForeignKey(JenisKendaraan, on_delete=models.CASCADE, blank=True, null=True)
    
    METODE_CHOICES = [
        ('SES', 'Simple Exponential Smoothing'),
        ('DES', 'Double Exponential Smoothing (Holt)'),
        ('TES', 'Triple Exponential Smoothing (Holt-Winters)'),
    ]
    
    # Periode Prediksi
    tahun_prediksi = models.IntegerField(db_index=True)
    bulan_prediksi = models.IntegerField(db_index=True)
    
    # Metode
    metode = models.CharField(max_length=10, choices=METODE_CHOICES)
    
    # Hasil Prediksi
    nilai_prediksi = models.DecimalField(max_digits=20, decimal_places=2)
    
    # Parameter Model
    alpha = models.DecimalField(max_digits=5, decimal_places=4, blank=True, null=True)
    beta = models.DecimalField(max_digits=5, decimal_places=4, blank=True, null=True)
    gamma = models.DecimalField(max_digits=5, decimal_places=4, blank=True, null=True)
    seasonal_periods = models.IntegerField(default=12, blank=True, null=True)
    
    # Metrik Evaluasi
    mape = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True, help_text="Mean Absolute Percentage Error")
    mae = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True, help_text="Mean Absolute Error")
    rmse = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True, help_text="Root Mean Squared Error")
    
    # Data Aktual (untuk perbandingan)
    nilai_aktual = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    
    # Metadata
    tanggal_prediksi = models.DateTimeField(auto_now_add=True)
    data_training_dari = models.DateField()
    data_training_sampai = models.DateField()
    jumlah_data_training = models.IntegerField()
    keterangan = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'hasil_prediksi'
        verbose_name = 'Hasil Prediksi'
        verbose_name_plural = 'Hasil Prediksi'
        ordering = ['-tahun_prediksi', '-bulan_prediksi']
        indexes = [
            models.Index(fields=['tahun_prediksi', 'bulan_prediksi']),
            models.Index(fields=['metode']),
        ]
    
    def __str__(self):
        return f"{self.metode} - {self.tahun_prediksi}-{self.bulan_prediksi:02d} - Rp {self.nilai_prediksi:,.0f}"
    
    @property
    def akurasi_persen(self):
        """Menghitung akurasi dalam persen"""
        if self.mape:
            return 100 - float(self.mape)
        return None
    
    @property
    def selisih(self):
        """Menghitung selisih antara aktual dan prediksi"""
        if self.nilai_aktual:
            return float(self.nilai_aktual - self.nilai_prediksi)
        return None