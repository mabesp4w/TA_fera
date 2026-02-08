from rest_framework import serializers
from crud.models import TransaksiPajak, KendaraanBermotor
from decimal import Decimal


class TransaksiPajakSerializer(serializers.ModelSerializer):
    """
    Serializer untuk TransaksiPajak
    """
    kendaraan_no_polisi = serializers.CharField(source='kendaraan.no_polisi', read_only=True)
    kendaraan_merek_nama = serializers.CharField(source='kendaraan.type_kendaraan.merek.nama', read_only=True)
    kendaraan_type_nama = serializers.CharField(source='kendaraan.type_kendaraan.nama', read_only=True)
    kendaraan_jenis_nama = serializers.CharField(source='kendaraan.jenis.nama', read_only=True)
    kendaraan_jenis_kategori = serializers.CharField(source='kendaraan.jenis.kategori', read_only=True)
    
    class Meta:
        model = TransaksiPajak
        fields = [
            'id', 'kendaraan', 'kendaraan_no_polisi', 'kendaraan_merek_nama', 'kendaraan_type_nama',
            'kendaraan_jenis_nama', 'kendaraan_jenis_kategori',
            'tahun', 'bulan', 'tgl_pajak',
            'jml_tahun_bayar', 'jml_bulan_bayar', 'tgl_bayar',
            # PKB
            'pokok_pkb', 'denda_pkb', 'tunggakan_pokok_pkb', 'tunggakan_denda_pkb',
            # OPSEN PKB
            'opsen_pokok_pkb', 'opsen_denda_pkb',
            # SWDKLLJ
            'pokok_swdkllj', 'denda_swdkllj', 'tunggakan_pokok_swdkllj', 'tunggakan_denda_swdkllj',
            # BBNKB
            'pokok_bbnkb', 'denda_bbnkb', 'total_bbnkb',
            # OPSEN BBNKB
            'opsen_pokok_bbnkb', 'opsen_denda_bbnkb',
            # TOTAL
            'total_bayar',
            # Metadata
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'total_bayar', 'created_at', 'updated_at',
            'kendaraan_no_polisi', 'kendaraan_merek_nama', 'kendaraan_type_nama',
            'kendaraan_jenis_nama', 'kendaraan_jenis_kategori'
        ]
    
    def validate_kendaraan(self, value):
        """
        Validasi kendaraan harus ada
        """
        if not value:
            raise serializers.ValidationError("Kendaraan harus dipilih.")
        
        if not KendaraanBermotor.objects.filter(pk=value.pk).exists():
            raise serializers.ValidationError("Kendaraan tidak ditemukan.")
        
        return value
    
    def validate_tahun(self, value):
        """
        Validasi tahun >= 2000
        """
        if value < 2000:
            raise serializers.ValidationError("Tahun harus >= 2000.")
        return value
    
    def validate_bulan(self, value):
        """
        Validasi bulan antara 1-12
        """
        if value < 1 or value > 12:
            raise serializers.ValidationError("Bulan harus antara 1 dan 12.")
        return value
    
    def validate_jml_tahun_bayar(self, value):
        """
        Validasi jumlah tahun bayar >= 0
        """
        if value < 0:
            raise serializers.ValidationError("Jumlah tahun bayar tidak boleh negatif.")
        return value
    
    def validate_jml_bulan_bayar(self, value):
        """
        Validasi jumlah bulan bayar >= 0
        """
        if value < 0:
            raise serializers.ValidationError("Jumlah bulan bayar tidak boleh negatif.")
        return value
    
    def validate(self, attrs):
        """
        Validasi kombinasi kendaraan, tahun, bulan harus unik
        """
        kendaraan = attrs.get('kendaraan')
        tahun = attrs.get('tahun')
        bulan = attrs.get('bulan')
        instance = self.instance
        
        if kendaraan and tahun and bulan:
            # Cek apakah kombinasi kendaraan + tahun + bulan sudah ada
            queryset = TransaksiPajak.objects.filter(
                kendaraan=kendaraan,
                tahun=tahun,
                bulan=bulan
            )
            
            if instance:
                # Update: cek duplikat kecuali instance sendiri
                queryset = queryset.exclude(pk=instance.pk)
            
            if queryset.exists():
                raise serializers.ValidationError(
                    f"Transaksi pajak untuk kendaraan '{kendaraan.no_polisi}' pada periode {tahun}-{bulan:02d} sudah ada."
                )
        
        return attrs
    
    def save(self, **kwargs):
        """
        Override save untuk memastikan total_bayar dihitung
        (sebenarnya sudah di-handle di model save, tapi kita pastikan)
        """
        instance = super().save(**kwargs)
        # total_bayar akan dihitung otomatis di model save()
        return instance

