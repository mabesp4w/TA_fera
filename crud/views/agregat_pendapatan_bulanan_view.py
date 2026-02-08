from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q, F
from django.db import transaction

from crud.models import AgregatPendapatanBulanan, TransaksiPajak, JenisKendaraan
from crud.serializers.agregat_pendapatan_bulanan_serializer import AgregatPendapatanBulananSerializer
from crud.utils.response import APIResponse
from crud.utils.permissions import IsAdmin
from decimal import Decimal


class AgregatPendapatanBulananListView(APIView):
    """
    API endpoint untuk list AgregatPendapatanBulanan (Read-only)
    GET: List semua agregat pendapatan bulanan
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        """
        Get list semua agregat pendapatan bulanan dengan pagination dan filter
        """
        try:
            # Get query parameters
            page = request.query_params.get('page', 1)
            page_size = request.query_params.get('page_size', 10)
            tahun = request.query_params.get('tahun', '')
            bulan = request.query_params.get('bulan', '')
            jenis_kendaraan_id = request.query_params.get('jenis_kendaraan_id', '')
            
            # Query base dengan select_related untuk optimasi
            # Exclude record global (jenis_kendaraan=NULL) yang digunakan khusus untuk prediksi
            queryset = AgregatPendapatanBulanan.objects.select_related('jenis_kendaraan').filter(
                jenis_kendaraan__isnull=False
            )
            
            # Filter by tahun
            if tahun:
                queryset = queryset.filter(tahun=tahun)
            
            # Filter by bulan
            if bulan:
                queryset = queryset.filter(bulan=bulan)
            
            # Filter by jenis_kendaraan
            if jenis_kendaraan_id:
                queryset = queryset.filter(jenis_kendaraan_id=jenis_kendaraan_id)
            
            # Ordering
            queryset = queryset.order_by('-tahun', '-bulan', 'jenis_kendaraan__nama')
            
            # Pagination
            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page)
            
            # Serialize data
            serializer = AgregatPendapatanBulananSerializer(page_obj, many=True)
            
            # Response dengan pagination info
            return APIResponse.paginated_success(
                data=serializer.data,
                message='Data agregat pendapatan bulanan berhasil diambil',
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
                message='Terjadi kesalahan saat mengambil data agregat pendapatan bulanan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AgregatPendapatanBulananDetailView(APIView):
    """
    API endpoint untuk detail AgregatPendapatanBulanan (Read-only)
    GET: Get detail agregat pendapatan bulanan
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get_object(self, pk):
        """
        Helper method untuk get object atau raise 404
        """
        try:
            return AgregatPendapatanBulanan.objects.select_related('jenis_kendaraan').get(pk=pk)
        except AgregatPendapatanBulanan.DoesNotExist:
            return None
    
    def get(self, request, pk):
        """
        Get detail agregat pendapatan bulanan
        """
        try:
            agregat = self.get_object(pk)
            
            if not agregat:
                return APIResponse.error(
                    message='Agregat pendapatan bulanan tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            serializer = AgregatPendapatanBulananSerializer(agregat)
            return APIResponse.success(
                data=serializer.data,
                message='Data agregat pendapatan bulanan berhasil diambil'
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengambil data agregat pendapatan bulanan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AgregatPendapatanBulananRegenerateView(APIView):
    """
    API endpoint untuk regenerate AgregatPendapatanBulanan dari TransaksiPajak
    POST: Regenerate agregat pendapatan bulanan
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    @staticmethod
    def _generate_global_records():
        """
        Generate record global (jenis_kendaraan=NULL) dari SUM per-jenis records.
        Karena data TransaksiPajak sudah di-smoothing, cukup menjumlahkan
        record per-jenis untuk mendapatkan total bulanan yang konsisten.
        """
        monthly_totals = AgregatPendapatanBulanan.objects.filter(
            jenis_kendaraan__isnull=False
        ).values('tahun', 'bulan').annotate(
            total_pendapatan=Sum('total_pendapatan'),
            total_pokok_pkb=Sum('total_pokok_pkb'),
            total_denda_pkb=Sum('total_denda_pkb'),
            total_swdkllj=Sum('total_swdkllj'),
            total_bbnkb=Sum('total_bbnkb'),
            total_opsen=Sum('total_opsen'),
            sum_transaksi=Sum('jumlah_transaksi'),
            sum_kendaraan=Sum('jumlah_kendaraan'),
        ).order_by('tahun', 'bulan')
        
        created = 0
        for m in monthly_totals:
            AgregatPendapatanBulanan.objects.create(
                tahun=m['tahun'],
                bulan=m['bulan'],
                jenis_kendaraan=None,
                total_pendapatan=m['total_pendapatan'] or Decimal('0'),
                total_pokok_pkb=m['total_pokok_pkb'] or Decimal('0'),
                total_denda_pkb=m['total_denda_pkb'] or Decimal('0'),
                total_swdkllj=m['total_swdkllj'] or Decimal('0'),
                total_bbnkb=m['total_bbnkb'] or Decimal('0'),
                total_opsen=m['total_opsen'] or Decimal('0'),
                jumlah_transaksi=m['sum_transaksi'] or 0,
                jumlah_kendaraan=m['sum_kendaraan'] or 0,
            )
            created += 1
        
        return created
    
    def post(self, request):
        """
        Regenerate agregat pendapatan bulanan dari TransaksiPajak
        Query params:
        - tahun (optional): Regenerate untuk tahun tertentu
        - bulan (optional): Regenerate untuk bulan tertentu
        - jenis_kendaraan_id (optional): Regenerate untuk jenis kendaraan tertentu
        - all (optional): Regenerate semua data
        """
        try:
            tahun = request.query_params.get('tahun', '')
            bulan = request.query_params.get('bulan', '')
            jenis_kendaraan_id = request.query_params.get('jenis_kendaraan_id', '')
            
            # Bisa dari query params atau body
            all_param = request.query_params.get('all', '')
            if not all_param and request.data:
                all_param = request.data.get('all', '')
                if not all_param and request.data.get('regenerate_all'):
                    all_param = 'true'
            regenerate_all = all_param.lower() == 'true'
            
            # Build filter untuk TransaksiPajak
            transaksi_filter = {}
            if tahun:
                transaksi_filter['tahun'] = tahun
            if bulan:
                transaksi_filter['bulan'] = bulan
            
            # Query TransaksiPajak dengan aggregasi per jenis kendaraan
            queryset = TransaksiPajak.objects.filter(
                kendaraan__isnull=False
            ).values(
                'tahun', 'bulan', 'kendaraan__jenis'
            ).annotate(
                total_pendapatan=Sum('total_bayar'),
                total_pokok_pkb=Sum('pokok_pkb'),
                total_denda_pkb=Sum('denda_pkb'),
                total_swdkllj=Sum(F('pokok_swdkllj') + F('denda_swdkllj')),
                total_bbnkb=Sum(F('pokok_bbnkb') + F('denda_bbnkb')),
                total_opsen=Sum(
                    F('opsen_pokok_pkb') + F('opsen_denda_pkb') + 
                    F('opsen_pokok_bbnkb') + F('opsen_denda_bbnkb')
                ),
                jumlah_transaksi=Count('id'),
                jumlah_kendaraan=Count('kendaraan', distinct=True)
            ).order_by('tahun', 'bulan', 'kendaraan__jenis')
            
            # Apply filters
            if transaksi_filter:
                queryset = queryset.filter(**transaksi_filter)
            
            # Filter by jenis_kendaraan jika ada
            if jenis_kendaraan_id:
                queryset = queryset.filter(kendaraan__jenis_id=jenis_kendaraan_id)
            
            # Jika regenerate_all, hapus semua data terlebih dahulu
            deleted_count = 0
            if regenerate_all:
                count_before = AgregatPendapatanBulanan.objects.all().count()
                deleted, _ = AgregatPendapatanBulanan.objects.all().delete()
                deleted_count = deleted
            
            # Regenerate data per jenis kendaraan
            created_count = 0
            updated_count = 0
            
            with transaction.atomic():
                for item in queryset:
                    tahun_val = item['tahun']
                    bulan_val = item['bulan']
                    jenis_kendaraan_id_val = item['kendaraan__jenis']
                    
                    agregat, created = AgregatPendapatanBulanan.objects.get_or_create(
                        tahun=tahun_val,
                        bulan=bulan_val,
                        jenis_kendaraan_id=jenis_kendaraan_id_val,
                        defaults={
                            'total_pendapatan': item['total_pendapatan'] or Decimal('0'),
                            'total_pokok_pkb': item['total_pokok_pkb'] or Decimal('0'),
                            'total_denda_pkb': item['total_denda_pkb'] or Decimal('0'),
                            'total_swdkllj': item['total_swdkllj'] or Decimal('0'),
                            'total_bbnkb': item['total_bbnkb'] or Decimal('0'),
                            'total_opsen': item['total_opsen'] or Decimal('0'),
                            'jumlah_transaksi': item['jumlah_transaksi'] or 0,
                            'jumlah_kendaraan': item['jumlah_kendaraan'] or 0,
                        }
                    )
                    
                    if not created:
                        agregat.total_pendapatan = item['total_pendapatan'] or Decimal('0')
                        agregat.total_pokok_pkb = item['total_pokok_pkb'] or Decimal('0')
                        agregat.total_denda_pkb = item['total_denda_pkb'] or Decimal('0')
                        agregat.total_swdkllj = item['total_swdkllj'] or Decimal('0')
                        agregat.total_bbnkb = item['total_bbnkb'] or Decimal('0')
                        agregat.total_opsen = item['total_opsen'] or Decimal('0')
                        agregat.jumlah_transaksi = item['jumlah_transaksi'] or 0
                        agregat.jumlah_kendaraan = item['jumlah_kendaraan'] or 0
                        agregat.save()
                        updated_count += 1
                    else:
                        created_count += 1
                
                # PENTING: Generate record global (jenis_kendaraan=NULL) 
                # dengan data yang sudah di-smoothing untuk prediksi
                # Hapus record global yang lama dulu
                AgregatPendapatanBulanan.objects.filter(
                    jenis_kendaraan__isnull=True
                ).delete()
                
                # Generate record global baru
                global_created = self._generate_global_records()
                created_count += global_created
            
            return APIResponse.success(
                data={
                    'created': created_count,
                    'updated': updated_count,
                    'deleted': deleted_count,
                    'total': created_count + updated_count,
                    'global_records': global_created,
                },
                message=f'Agregat berhasil di-regenerate. Dibuat: {created_count} (termasuk {global_created} global), Diupdate: {updated_count}',
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat regenerate agregat pendapatan bulanan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AgregatPendapatanBulananFilterOptionsView(APIView):
    """
    API endpoint untuk mendapatkan filter options (tahun dan bulan)
    GET: Get list tahun dan bulan yang tersedia di database
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        """
        Get filter options untuk agregat pendapatan bulanan
        """
        try:
            # Get unique tahun yang tersedia di database (hanya yang memiliki jenis_kendaraan)
            tahun_list = AgregatPendapatanBulanan.objects.filter(
                jenis_kendaraan__isnull=False
            ).values_list('tahun', flat=True).distinct().order_by('-tahun')
            tahun_options = [{'value': t, 'label': str(t)} for t in tahun_list]
            
            # Get unique bulan yang tersedia di database (hanya yang memiliki jenis_kendaraan)
            bulan_list = AgregatPendapatanBulanan.objects.filter(
                jenis_kendaraan__isnull=False
            ).values_list('bulan', flat=True).distinct().order_by('bulan')
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


class AgregatPendapatanBulananSummaryView(APIView):
    """
    API endpoint untuk summary agregat pendapatan bulanan
    GET: Get summary total dari seluruh data (tanpa pagination)
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        """
        Get summary agregat pendapatan bulanan berdasarkan filter
        """
        try:
            tahun = request.query_params.get('tahun', '')
            bulan = request.query_params.get('bulan', '')
            jenis_kendaraan_id = request.query_params.get('jenis_kendaraan_id', '')
            
            # Base queryset - exclude record global
            queryset = AgregatPendapatanBulanan.objects.filter(
                jenis_kendaraan__isnull=False
            )
            
            # Apply filters
            if tahun:
                queryset = queryset.filter(tahun=tahun)
            
            if bulan:
                queryset = queryset.filter(bulan=bulan)
            
            if jenis_kendaraan_id:
                queryset = queryset.filter(jenis_kendaraan_id=jenis_kendaraan_id)
            
            # Calculate summary
            summary = queryset.aggregate(
                total_pendapatan=Sum('total_pendapatan'),
                total_pokok_pkb=Sum('total_pokok_pkb'),
                total_denda_pkb=Sum('total_denda_pkb'),
                total_swdkllj=Sum('total_swdkllj'),
                total_bbnkb=Sum('total_bbnkb'),
                total_opsen=Sum('total_opsen'),
                jumlah_transaksi=Sum('jumlah_transaksi'),
                jumlah_kendaraan=Sum('jumlah_kendaraan'),
                jumlah_periode=Count('id')
            )
            
            # Format summary
            formatted_summary = {
                'total_pendapatan': float(summary['total_pendapatan'] or 0),
                'total_pokok_pkb': float(summary['total_pokok_pkb'] or 0),
                'total_denda_pkb': float(summary['total_denda_pkb'] or 0),
                'total_swdkllj': float(summary['total_swdkllj'] or 0),
                'total_bbnkb': float(summary['total_bbnkb'] or 0),
                'total_opsen': float(summary['total_opsen'] or 0),
                'jumlah_transaksi': summary['jumlah_transaksi'] or 0,
                'jumlah_kendaraan': summary['jumlah_kendaraan'] or 0,
                'jumlah_periode': summary['jumlah_periode'] or 0,
            }
            
            return APIResponse.success(
                data=formatted_summary,
                message='Summary agregat pendapatan bulanan berhasil diambil'
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengambil summary agregat pendapatan bulanan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


