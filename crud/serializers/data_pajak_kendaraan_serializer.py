from rest_framework import serializers
from decimal import Decimal
from crud.models import DataPajakKendaraan, KendaraanBermotor


class DataPajakKendaraanSerializer(serializers.ModelSerializer):
    """
    Serializer untuk DataPajakKendaraan
    """
    kendaraan_no_polisi = serializers.CharField(source='kendaraan.no_polisi', read_only=True)
    kendaraan_merek_nama = serializers.CharField(source='kendaraan.type_kendaraan.merek.nama', read_only=True)
    kendaraan_type_nama = serializers.CharField(source='kendaraan.type_kendaraan.nama', read_only=True)
    
    class Meta:
        model = DataPajakKendaraan
        fields = [
            'id', 'kendaraan', 'kendaraan_no_polisi', 'kendaraan_merek_nama', 'kendaraan_type_nama',
            'njkb_saat_ini', 'bobot_saat_ini', 'dp_pkb_saat_ini', 'tarif_pkb_saat_ini',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'dp_pkb_saat_ini', 'created_at', 'updated_at',
            'kendaraan_no_polisi', 'kendaraan_merek_nama', 'kendaraan_type_nama'
        ]
    
    def validate_kendaraan(self, value):
        """
        Validasi kendaraan harus ada dan belum punya data pajak (untuk create)
        """
        if not value:
            raise serializers.ValidationError("Kendaraan harus dipilih.")
        
        # Cek apakah kendaraan ada di database
        if not KendaraanBermotor.objects.filter(pk=value.pk).exists():
            raise serializers.ValidationError("Kendaraan tidak ditemukan.")
        
        # Untuk create, cek apakah kendaraan sudah punya data pajak
        instance = self.instance
        if not instance:
            # Create: cek apakah kendaraan sudah punya data pajak
            if DataPajakKendaraan.objects.filter(kendaraan=value).exists():
                raise serializers.ValidationError(
                    f"Kendaraan dengan nomor polisi '{value.no_polisi}' sudah memiliki data pajak."
                )
        
        return value
    
    def validate_njkb_saat_ini(self, value):
        """
        Validasi NJKB harus >= 0
        """
        if value is not None and value < 0:
            raise serializers.ValidationError("NJKB tidak boleh negatif.")
        return value
    
    def validate_bobot_saat_ini(self, value):
        """
        Validasi bobot harus > 0
        """
        if value is not None and value <= 0:
            raise serializers.ValidationError("Bobot harus lebih besar dari 0.")
        return value
    
    def validate_tarif_pkb_saat_ini(self, value):
        """
        Validasi tarif PKB harus >= 0 dan <= 100
        """
        if value is not None:
            if value < 0:
                raise serializers.ValidationError("Tarif PKB tidak boleh negatif.")
            if value > 100:
                raise serializers.ValidationError("Tarif PKB tidak boleh lebih dari 100%.")
        return value
    
    def save(self, **kwargs):
        """
        Override save untuk auto-calculate dp_pkb_saat_ini
        """
        instance = super().save(**kwargs)
        # Auto calculate DP PKB (sudah di-handle di model save, tapi kita pastikan)
        if instance.njkb_saat_ini and instance.bobot_saat_ini:
            instance.dp_pkb_saat_ini = instance.njkb_saat_ini * instance.bobot_saat_ini
            instance.save(update_fields=['dp_pkb_saat_ini'])
        return instance

