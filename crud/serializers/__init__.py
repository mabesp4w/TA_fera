from .jenis_kendaraan_serializer import JenisKendaraanSerializer
from .kecamatan_serializer import KecamatanSerializer
from .kelurahan_serializer import KelurahanSerializer
from .merek_kendaraan_serializer import MerekKendaraanSerializer
from .type_kendaraan_serializer import TypeKendaraanSerializer
from .wajib_pajak_serializer import WajibPajakSerializer
from .kendaraan_bermotor_serializer import KendaraanBermotorSerializer
from .data_pajak_kendaraan_serializer import DataPajakKendaraanSerializer
from .transaksi_pajak_serializer import TransaksiPajakSerializer
from .agregat_pendapatan_bulanan_serializer import AgregatPendapatanBulananSerializer
from .hasil_prediksi_serializer import HasilPrediksiSerializer

__all__ = [
    'JenisKendaraanSerializer', 
    'KecamatanSerializer', 
    'KelurahanSerializer',
    'MerekKendaraanSerializer',
    'TypeKendaraanSerializer',
    'WajibPajakSerializer',
    'KendaraanBermotorSerializer',
    'DataPajakKendaraanSerializer',
    'TransaksiPajakSerializer',
    'AgregatPendapatanBulananSerializer',
    'HasilPrediksiSerializer'
]
