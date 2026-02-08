from rest_framework import serializers
from crud.models import AgregatPendapatanBulanan


class AgregatPendapatanBulananSerializer(serializers.ModelSerializer):
    """
    Serializer untuk AgregatPendapatanBulanan (Read-only)
    """
    jenis_kendaraan_nama = serializers.CharField(source='jenis_kendaraan.nama', read_only=True)
    jenis_kendaraan_kategori = serializers.CharField(source='jenis_kendaraan.kategori', read_only=True)
    
    class Meta:
        model = AgregatPendapatanBulanan
        fields = [
            'id', 'jenis_kendaraan', 'jenis_kendaraan_nama', 'jenis_kendaraan_kategori',
            'tahun', 'bulan',
            'total_pendapatan', 'total_pokok_pkb', 'total_denda_pkb',
            'total_swdkllj', 'total_bbnkb', 'total_opsen',
            'jumlah_transaksi', 'jumlah_kendaraan',
            'tanggal_agregasi'
        ]

