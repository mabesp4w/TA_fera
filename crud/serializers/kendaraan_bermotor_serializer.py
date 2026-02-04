from rest_framework import serializers
from crud.models import KendaraanBermotor, JenisKendaraan, TypeKendaraan, WajibPajak


class KendaraanBermotorSerializer(serializers.ModelSerializer):
    """
    Serializer untuk KendaraanBermotor
    """
    jenis_nama = serializers.CharField(source='jenis.nama', read_only=True)
    jenis_kategori = serializers.CharField(source='jenis.kategori', read_only=True)
    merek_nama = serializers.CharField(source='type_kendaraan.merek.nama', read_only=True)
    type_kendaraan_nama = serializers.CharField(source='type_kendaraan.nama', read_only=True)
    wajib_pajak_nama = serializers.CharField(source='wajib_pajak.nama', read_only=True)
    bbm_display = serializers.CharField(source='get_bbm_display', read_only=True)
    
    class Meta:
        model = KendaraanBermotor
        fields = [
            'id', 'no_polisi', 'no_rangka', 'no_mesin',
            'jenis', 'jenis_nama', 'jenis_kategori',
            'merek_nama',
            'type_kendaraan', 'type_kendaraan_nama',
            'wajib_pajak', 'wajib_pajak_nama',
            'tahun_buat', 'jml_cc', 'bbm', 'bbm_display',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'jenis_nama', 'jenis_kategori', 'merek_nama',
            'type_kendaraan_nama', 'wajib_pajak_nama', 'bbm_display'
        ]
    
    def validate_no_polisi(self, value):
        """
        Validasi no_polisi harus unik
        """
        instance = self.instance
        if instance:
            # Update: cek duplikat kecuali instance sendiri
            if KendaraanBermotor.objects.filter(no_polisi=value).exclude(pk=instance.pk).exists():
                raise serializers.ValidationError("Nomor polisi sudah terdaftar.")
        else:
            # Create: cek duplikat
            if KendaraanBermotor.objects.filter(no_polisi=value).exists():
                raise serializers.ValidationError("Nomor polisi sudah terdaftar.")
        return value
    
    def validate_no_rangka(self, value):
        """
        Validasi no_rangka harus unik
        """
        instance = self.instance
        if instance:
            # Update: cek duplikat kecuali instance sendiri
            if KendaraanBermotor.objects.filter(no_rangka=value).exclude(pk=instance.pk).exists():
                raise serializers.ValidationError("Nomor rangka sudah terdaftar.")
        else:
            # Create: cek duplikat
            if KendaraanBermotor.objects.filter(no_rangka=value).exists():
                raise serializers.ValidationError("Nomor rangka sudah terdaftar.")
        return value
    
    def validate_jenis(self, value):
        """Validasi jenis kendaraan harus ada"""
        if not value:
            raise serializers.ValidationError("Jenis kendaraan harus dipilih.")
        if not JenisKendaraan.objects.filter(pk=value.pk).exists():
            raise serializers.ValidationError("Jenis kendaraan tidak ditemukan.")
        return value
    
    def validate_type_kendaraan(self, value):
        """Validasi type kendaraan harus ada"""
        if not value:
            raise serializers.ValidationError("Type kendaraan harus dipilih.")
        if not TypeKendaraan.objects.filter(pk=value.pk).exists():
            raise serializers.ValidationError("Type kendaraan tidak ditemukan.")
        return value
    
    def validate_wajib_pajak(self, value):
        """Validasi wajib pajak harus ada"""
        if not value:
            raise serializers.ValidationError("Wajib pajak harus dipilih.")
        if not WajibPajak.objects.filter(pk=value.pk).exists():
            raise serializers.ValidationError("Wajib pajak tidak ditemukan.")
        return value
    
    def validate_tahun_buat(self, value):
        """Validasi tahun buat"""
        if value < 1900 or value > 2100:
            raise serializers.ValidationError("Tahun buat harus antara 1900 dan 2100.")
        return value
    
    def validate_bbm(self, value):
        """Validasi BBM"""
        valid_bbm = ['BENSIN', 'SOLAR', 'LISTRIK', 'HYBRID']
        if value not in valid_bbm:
            raise serializers.ValidationError(
                f"BBM harus salah satu dari: {', '.join(valid_bbm)}"
            )
        return value
