from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q, F

from crud.models import TransaksiPajak, KendaraanBermotor
from crud.utils.response import APIResponse
from crud.utils.permissions import IsAdmin


class LaporanTotalPajakView(APIView):
    """
    API endpoint untuk laporan total pajak per tahun, bulan, dan kendaraan
    GET: List total pajak dengan grouping per kendaraan per periode
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        """
        Get laporan total pajak dengan pagination dan filter
        Query params:
        - page: halaman (default: 1)
        - page_size: jumlah item per halaman (default: 10)
        - tahun: filter by tahun
        - bulan: filter by bulan
        - kendaraan_id: filter by kendaraan
        - jenis_kendaraan_id: filter by jenis kendaraan
        - search: search by no_polisi
        """
        try:
            # Get query parameters
            page = request.query_params.get('page', 1)
            page_size = request.query_params.get('page_size', 10)
            tahun = request.query_params.get('tahun', '')
            bulan = request.query_params.get('bulan', '')
            kendaraan_id = request.query_params.get('kendaraan_id', '')
            jenis_kendaraan_id = request.query_params.get('jenis_kendaraan_id', '')
            search = request.query_params.get('search', '')
            
            # Query dengan annotasi untuk menghitung total pajak per kendaraan per periode
            queryset = TransaksiPajak.objects.select_related(
                'kendaraan',
                'kendaraan__jenis',
                'kendaraan__type_kendaraan',
                'kendaraan__type_kendaraan__merek',
                'kendaraan__wajib_pajak'
            ).values(
                'kendaraan_id',
                'kendaraan__no_polisi',
                'kendaraan__jenis__nama',
                'kendaraan__jenis__kategori',
                'kendaraan__type_kendaraan__nama',
                'kendaraan__type_kendaraan__merek__nama',
                'kendaraan__wajib_pajak__nama',
                'tahun',
                'bulan'
            ).annotate(
                total_pokok_pkb=Sum('pokok_pkb'),
                total_denda_pkb=Sum('denda_pkb'),
                total_tunggakan_pokok_pkb=Sum('tunggakan_pokok_pkb'),
                total_tunggakan_denda_pkb=Sum('tunggakan_denda_pkb'),
                total_opsen_pokok_pkb=Sum('opsen_pokok_pkb'),
                total_opsen_denda_pkb=Sum('opsen_denda_pkb'),
                total_pokok_swdkllj=Sum('pokok_swdkllj'),
                total_denda_swdkllj=Sum('denda_swdkllj'),
                total_tunggakan_pokok_swdkllj=Sum('tunggakan_pokok_swdkllj'),
                total_tunggakan_denda_swdkllj=Sum('tunggakan_denda_swdkllj'),
                total_pokok_bbnkb=Sum('pokok_bbnkb'),
                total_denda_bbnkb=Sum('denda_bbnkb'),
                total_opsen_pokok_bbnkb=Sum('opsen_pokok_bbnkb'),
                total_opsen_denda_bbnkb=Sum('opsen_denda_bbnkb'),
                total_bayar=Sum('total_bayar'),
                jumlah_transaksi=Count('id')
            ).order_by('-tahun', '-bulan', 'kendaraan__no_polisi')
            
            # Apply filters dengan konversi tipe data yang benar
            if tahun:
                try:
                    tahun_int = int(tahun)
                    queryset = queryset.filter(tahun=tahun_int)
                except (ValueError, TypeError):
                    pass
            
            if bulan:
                try:
                    bulan_int = int(bulan)
                    queryset = queryset.filter(bulan=bulan_int)
                except (ValueError, TypeError):
                    pass
            
            if kendaraan_id:
                try:
                    kendaraan_id_int = int(kendaraan_id)
                    queryset = queryset.filter(kendaraan_id=kendaraan_id_int)
                except (ValueError, TypeError):
                    pass
            
            if jenis_kendaraan_id:
                try:
                    jenis_id_int = int(jenis_kendaraan_id)
                    queryset = queryset.filter(kendaraan__jenis_id=jenis_id_int)
                except (ValueError, TypeError):
                    pass
            
            if search:
                queryset = queryset.filter(
                    Q(kendaraan__no_polisi__icontains=search) |
                    Q(kendaraan__wajib_pajak__nama__icontains=search)
                )
            
            # Pagination
            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page)
            
            # Format data untuk response
            formatted_data = []
            for item in page_obj:
                formatted_data.append({
                    'id': f"{item['kendaraan_id']}_{item['tahun']}_{item['bulan']}",
                    'kendaraan_id': item['kendaraan_id'],
                    'no_polisi': item['kendaraan__no_polisi'],
                    'jenis_kendaraan': item['kendaraan__jenis__nama'],
                    'kategori_kendaraan': item['kendaraan__jenis__kategori'],
                    'merek': item['kendaraan__type_kendaraan__merek__nama'],
                    'type_kendaraan': item['kendaraan__type_kendaraan__nama'],
                    'nama_pemilik': item['kendaraan__wajib_pajak__nama'],
                    'tahun': item['tahun'],
                    'bulan': item['bulan'],
                    'nama_bulan': self.get_bulan_nama(item['bulan']),
                    'total_pokok_pkb': float(item['total_pokok_pkb'] or 0),
                    'total_denda_pkb': float(item['total_denda_pkb'] or 0),
                    'total_tunggakan_pokok_pkb': float(item['total_tunggakan_pokok_pkb'] or 0),
                    'total_tunggakan_denda_pkb': float(item['total_tunggakan_denda_pkb'] or 0),
                    'total_opsen_pokok_pkb': float(item['total_opsen_pokok_pkb'] or 0),
                    'total_opsen_denda_pkb': float(item['total_opsen_denda_pkb'] or 0),
                    'total_pokok_swdkllj': float(item['total_pokok_swdkllj'] or 0),
                    'total_denda_swdkllj': float(item['total_denda_swdkllj'] or 0),
                    'total_tunggakan_pokok_swdkllj': float(item['total_tunggakan_pokok_swdkllj'] or 0),
                    'total_tunggakan_denda_swdkllj': float(item['total_tunggakan_denda_swdkllj'] or 0),
                    'total_pokok_bbnkb': float(item['total_pokok_bbnkb'] or 0),
                    'total_denda_bbnkb': float(item['total_denda_bbnkb'] or 0),
                    'total_opsen_pokok_bbnkb': float(item['total_opsen_pokok_bbnkb'] or 0),
                    'total_opsen_denda_bbnkb': float(item['total_opsen_denda_bbnkb'] or 0),
                    'total_pkb': float(
                        (item['total_pokok_pkb'] or 0) + 
                        (item['total_denda_pkb'] or 0) +
                        (item['total_tunggakan_pokok_pkb'] or 0) +
                        (item['total_tunggakan_denda_pkb'] or 0)
                    ),
                    'total_swdkllj': float(
                        (item['total_pokok_swdkllj'] or 0) + 
                        (item['total_denda_swdkllj'] or 0) +
                        (item['total_tunggakan_pokok_swdkllj'] or 0) +
                        (item['total_tunggakan_denda_swdkllj'] or 0)
                    ),
                    'total_bbnkb': float(
                        (item['total_pokok_bbnkb'] or 0) + 
                        (item['total_denda_bbnkb'] or 0)
                    ),
                    'total_opsen': float(
                        (item['total_opsen_pokok_pkb'] or 0) + 
                        (item['total_opsen_denda_pkb'] or 0) +
                        (item['total_opsen_pokok_bbnkb'] or 0) + 
                        (item['total_opsen_denda_bbnkb'] or 0)
                    ),
                    'total_bayar': float(item['total_bayar'] or 0),
                    'jumlah_transaksi': item['jumlah_transaksi'],
                })
            
            # Response dengan pagination info
            return APIResponse.paginated_success(
                data=formatted_data,
                message='Data laporan total pajak berhasil diambil',
                pagination_data={
                    'page': page_obj.number,
                    'page_size': int(page_size),
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous(),
                }
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengambil data laporan total pajak',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get_bulan_nama(self, bulan):
        """Helper method untuk mengkonversi nomor bulan ke nama bulan"""
        bulan_names = {
            1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
            5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
            9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
        }
        return bulan_names.get(bulan, '')


class LaporanTotalPajakFilterOptionsView(APIView):
    """
    API endpoint untuk mendapatkan filter options (tahun dan bulan)
    GET: Get list tahun dan bulan yang tersedia di database
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        """
        Get filter options untuk laporan total pajak
        """
        try:
            # Get unique tahun yang tersedia di database
            tahun_list = TransaksiPajak.objects.values_list('tahun', flat=True).distinct().order_by('-tahun')
            tahun_options = [{'value': t, 'label': str(t)} for t in tahun_list]
            
            # Get unique bulan yang tersedia di database
            bulan_list = TransaksiPajak.objects.values_list('bulan', flat=True).distinct().order_by('bulan')
            bulan_names = {
                1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
                5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
                9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
            }
            bulan_options = [{'value': b, 'label': bulan_names.get(b, str(b))} for b in bulan_list]
            
            return APIResponse.success(
                data={
                    'tahun_options': tahun_options,
                    'bulan_options': bulan_options
                },
                message='Filter options berhasil diambil'
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengambil filter options',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LaporanTotalPajakSummaryView(APIView):
    """
    API endpoint untuk summary laporan total pajak
    GET: Get summary total pajak berdasarkan filter
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        """
        Get summary laporan total pajak
        """
        try:
            tahun = request.query_params.get('tahun', '')
            bulan = request.query_params.get('bulan', '')
            jenis_kendaraan_id = request.query_params.get('jenis_kendaraan_id', '')
            
            # Base queryset
            queryset = TransaksiPajak.objects.all()
            
            # Apply filters dengan konversi tipe data yang benar
            if tahun:
                try:
                    tahun_int = int(tahun)
                    queryset = queryset.filter(tahun=tahun_int)
                except (ValueError, TypeError):
                    pass
            
            if bulan:
                try:
                    bulan_int = int(bulan)
                    queryset = queryset.filter(bulan=bulan_int)
                except (ValueError, TypeError):
                    pass
            
            if jenis_kendaraan_id:
                try:
                    jenis_id_int = int(jenis_kendaraan_id)
                    queryset = queryset.filter(kendaraan__jenis_id=jenis_id_int)
                except (ValueError, TypeError):
                    pass
            
            # Calculate summary
            summary = queryset.aggregate(
                total_pokok_pkb=Sum('pokok_pkb'),
                total_denda_pkb=Sum('denda_pkb'),
                total_tunggakan_pokok_pkb=Sum('tunggakan_pokok_pkb'),
                total_tunggakan_denda_pkb=Sum('tunggakan_denda_pkb'),
                total_opsen_pokok_pkb=Sum('opsen_pokok_pkb'),
                total_opsen_denda_pkb=Sum('opsen_denda_pkb'),
                total_pokok_swdkllj=Sum('pokok_swdkllj'),
                total_denda_swdkllj=Sum('denda_swdkllj'),
                total_tunggakan_pokok_swdkllj=Sum('tunggakan_pokok_swdkllj'),
                total_tunggakan_denda_swdkllj=Sum('tunggakan_denda_swdkllj'),
                total_pokok_bbnkb=Sum('pokok_bbnkb'),
                total_denda_bbnkb=Sum('denda_bbnkb'),
                total_opsen_pokok_bbnkb=Sum('opsen_pokok_bbnkb'),
                total_opsen_denda_bbnkb=Sum('opsen_denda_bbnkb'),
                total_bayar=Sum('total_bayar'),
                jumlah_transaksi=Count('id'),
                jumlah_kendaraan=Count('kendaraan', distinct=True)
            )
            
            # Format summary
            formatted_summary = {
                'total_pokok_pkb': float(summary['total_pokok_pkb'] or 0),
                'total_denda_pkb': float(summary['total_denda_pkb'] or 0),
                'total_tunggakan_pokok_pkb': float(summary['total_tunggakan_pokok_pkb'] or 0),
                'total_tunggakan_denda_pkb': float(summary['total_tunggakan_denda_pkb'] or 0),
                'total_opsen_pokok_pkb': float(summary['total_opsen_pokok_pkb'] or 0),
                'total_opsen_denda_pkb': float(summary['total_opsen_denda_pkb'] or 0),
                'total_pokok_swdkllj': float(summary['total_pokok_swdkllj'] or 0),
                'total_denda_swdkllj': float(summary['total_denda_swdkllj'] or 0),
                'total_tunggakan_pokok_swdkllj': float(summary['total_tunggakan_pokok_swdkllj'] or 0),
                'total_tunggakan_denda_swdkllj': float(summary['total_tunggakan_denda_swdkllj'] or 0),
                'total_pokok_bbnkb': float(summary['total_pokok_bbnkb'] or 0),
                'total_denda_bbnkb': float(summary['total_denda_bbnkb'] or 0),
                'total_opsen_pokok_bbnkb': float(summary['total_opsen_pokok_bbnkb'] or 0),
                'total_opsen_denda_bbnkb': float(summary['total_opsen_denda_bbnkb'] or 0),
                'total_pkb': float(
                    (summary['total_pokok_pkb'] or 0) + 
                    (summary['total_denda_pkb'] or 0) +
                    (summary['total_tunggakan_pokok_pkb'] or 0) +
                    (summary['total_tunggakan_denda_pkb'] or 0)
                ),
                'total_swdkllj': float(
                    (summary['total_pokok_swdkllj'] or 0) + 
                    (summary['total_denda_swdkllj'] or 0) +
                    (summary['total_tunggakan_pokok_swdkllj'] or 0) +
                    (summary['total_tunggakan_denda_swdkllj'] or 0)
                ),
                'total_bbnkb': float(
                    (summary['total_pokok_bbnkb'] or 0) + 
                    (summary['total_denda_bbnkb'] or 0)
                ),
                'total_opsen': float(
                    (summary['total_opsen_pokok_pkb'] or 0) + 
                    (summary['total_opsen_denda_pkb'] or 0) +
                    (summary['total_opsen_pokok_bbnkb'] or 0) + 
                    (summary['total_opsen_denda_bbnkb'] or 0)
                ),
                'total_bayar': float(summary['total_bayar'] or 0),
                'jumlah_transaksi': summary['jumlah_transaksi'],
                'jumlah_kendaraan': summary['jumlah_kendaraan'],
            }
            
            return APIResponse.success(
                data=formatted_summary,
                message='Summary laporan total pajak berhasil diambil'
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengambil summary laporan total pajak',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
