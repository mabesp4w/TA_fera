from rest_framework import serializers
from crud.models import HasilPrediksi, JenisKendaraan
from decimal import Decimal


class HasilPrediksiSerializer(serializers.ModelSerializer):
    """
    Serializer untuk HasilPrediksi
    """
    jenis_kendaraan_nama = serializers.CharField(source='jenis_kendaraan.nama', read_only=True)
    jenis_kendaraan_kategori = serializers.CharField(source='jenis_kendaraan.kategori', read_only=True)
    metode_display = serializers.CharField(source='get_metode_display', read_only=True)
    akurasi_persen = serializers.ReadOnlyField()
    selisih = serializers.ReadOnlyField()
    
    class Meta:
        model = HasilPrediksi
        fields = [
            'id', 'jenis_kendaraan', 'jenis_kendaraan_nama', 'jenis_kendaraan_kategori',
            'tahun_prediksi', 'bulan_prediksi',
            'metode', 'metode_display',
            'nilai_prediksi',
            # Parameter Model
            'alpha', 'beta', 'gamma', 'seasonal_periods',
            # Metrik Evaluasi
            'mape', 'mae', 'rmse',
            # Data Aktual
            'nilai_aktual',
            # Metadata
            'tanggal_prediksi', 'data_training_dari', 'data_training_sampai',
            'jumlah_data_training', 'keterangan',
            # Computed
            'akurasi_persen', 'selisih'
        ]
        read_only_fields = [
            'id', 'tanggal_prediksi', 'akurasi_persen', 'selisih',
            'jenis_kendaraan_nama', 'jenis_kendaraan_kategori', 'metode_display'
        ]
    
    def validate_jenis_kendaraan(self, value):
        """
        Validasi jenis kendaraan harus ada jika diisi
        """
        if value and not JenisKendaraan.objects.filter(pk=value.pk).exists():
            raise serializers.ValidationError("Jenis kendaraan tidak ditemukan.")
        return value
    
    def validate_tahun_prediksi(self, value):
        """
        Validasi tahun prediksi >= 2000
        """
        if value < 2000:
            raise serializers.ValidationError("Tahun prediksi harus >= 2000.")
        return value
    
    def validate_bulan_prediksi(self, value):
        """
        Validasi bulan prediksi antara 1-12
        """
        if value < 1 or value > 12:
            raise serializers.ValidationError("Bulan prediksi harus antara 1 dan 12.")
        return value
    
    def validate_metode(self, value):
        """
        Validasi metode harus valid
        """
        valid_methods = ['SES', 'DES', 'TES']
        if value not in valid_methods:
            raise serializers.ValidationError(
                f"Metode harus salah satu dari: {', '.join(valid_methods)}"
            )
        return value
    
    def validate_alpha(self, value):
        """
        Validasi alpha antara 0-1
        """
        if value is not None and (value < 0 or value > 1):
            raise serializers.ValidationError("Alpha harus antara 0 dan 1.")
        return value
    
    def validate_beta(self, value):
        """
        Validasi beta antara 0-1
        """
        if value is not None and (value < 0 or value > 1):
            raise serializers.ValidationError("Beta harus antara 0 dan 1.")
        return value
    
    def validate_gamma(self, value):
        """
        Validasi gamma antara 0-1
        """
        if value is not None and (value < 0 or value > 1):
            raise serializers.ValidationError("Gamma harus antara 0 dan 1.")
        return value
    
    def validate_mape(self, value):
        """
        Validasi MAPE >= 0
        """
        if value is not None and value < 0:
            raise serializers.ValidationError("MAPE tidak boleh negatif.")
        return value
    
    def validate_mae(self, value):
        """
        Validasi MAE >= 0
        """
        if value is not None and value < 0:
            raise serializers.ValidationError("MAE tidak boleh negatif.")
        return value
    
    def validate_rmse(self, value):
        """
        Validasi RMSE >= 0
        """
        if value is not None and value < 0:
            raise serializers.ValidationError("RMSE tidak boleh negatif.")
        return value

