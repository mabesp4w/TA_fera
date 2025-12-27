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
            queryset = AgregatPendapatanBulanan.objects.select_related('jenis_kendaraan').all()
            
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
            regenerate_all = request.query_params.get('all', 'false').lower() == 'true'
            
            # Build filter untuk TransaksiPajak
            transaksi_filter = {}
            if tahun:
                transaksi_filter['tahun'] = tahun
            if bulan:
                transaksi_filter['bulan'] = bulan
            
            # Query TransaksiPajak dengan aggregasi
            queryset = TransaksiPajak.objects.values(
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
            if regenerate_all:
                AgregatPendapatanBulanan.objects.all().delete()
            
            # Regenerate data
            created_count = 0
            updated_count = 0
            
            with transaction.atomic():
                for item in queryset:
                    tahun_val = item['tahun']
                    bulan_val = item['bulan']
                    jenis_kendaraan_id_val = item['kendaraan__jenis']
                    
                    # Get or create
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
                        # Update existing
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
            
            return APIResponse.success(
                data={
                    'created': created_count,
                    'updated': updated_count,
                    'total': created_count + updated_count
                },
                message=f'Agregat pendapatan bulanan berhasil di-regenerate. Created: {created_count}, Updated: {updated_count}',
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat regenerate agregat pendapatan bulanan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

