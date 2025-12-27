from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.paginator import Paginator
from django.db.models import Q

from crud.models import KendaraanBermotor
from crud.serializers.kendaraan_bermotor_serializer import KendaraanBermotorSerializer
from crud.utils.response import APIResponse
from crud.utils.permissions import IsAdmin


class KendaraanBermotorListView(APIView):
    """
    API endpoint untuk list dan create KendaraanBermotor
    GET: List semua kendaraan bermotor (dengan pagination dan search)
    POST: Create kendaraan bermotor baru
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        """
        Get list semua kendaraan bermotor dengan pagination dan search
        """
        try:
            # Get query parameters
            page = request.query_params.get('page', 1)
            page_size = request.query_params.get('page_size', 10)
            search = request.query_params.get('search', '')
            no_polisi = request.query_params.get('no_polisi', '')
            jenis_id = request.query_params.get('jenis_id', '')
            merek_id = request.query_params.get('merek_id', '')
            wajib_pajak_id = request.query_params.get('wajib_pajak_id', '')
            
            # Query base dengan select_related untuk optimasi
            queryset = KendaraanBermotor.objects.select_related(
                'jenis', 'merek', 'type_kendaraan', 'wajib_pajak'
            ).all()
            
            # Filter by search (no_polisi, no_rangka, no_mesin, atau nama wajib pajak)
            if search:
                queryset = queryset.filter(
                    Q(no_polisi__icontains=search) |
                    Q(no_rangka__icontains=search) |
                    Q(no_mesin__icontains=search) |
                    Q(wajib_pajak__nama__icontains=search)
                )
            
            # Filter by no_polisi
            if no_polisi:
                queryset = queryset.filter(no_polisi__icontains=no_polisi)
            
            # Filter by jenis
            if jenis_id:
                queryset = queryset.filter(jenis_id=jenis_id)
            
            # Filter by merek
            if merek_id:
                queryset = queryset.filter(merek_id=merek_id)
            
            # Filter by wajib pajak
            if wajib_pajak_id:
                queryset = queryset.filter(wajib_pajak_id=wajib_pajak_id)
            
            # Ordering
            queryset = queryset.order_by('-created_at', 'no_polisi')
            
            # Pagination
            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page)
            
            # Serialize data
            serializer = KendaraanBermotorSerializer(page_obj, many=True)
            
            # Response dengan pagination info
            return APIResponse.paginated_success(
                data=serializer.data,
                message='Data kendaraan bermotor berhasil diambil',
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
                message='Terjadi kesalahan saat mengambil data kendaraan bermotor',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """
        Create kendaraan bermotor baru
        """
        try:
            serializer = KendaraanBermotorSerializer(data=request.data)
            
            if serializer.is_valid():
                kendaraan = serializer.save()
                return APIResponse.success(
                    data=KendaraanBermotorSerializer(kendaraan).data,
                    message='Kendaraan bermotor berhasil dibuat',
                    status_code=status.HTTP_201_CREATED
                )
            else:
                return APIResponse.error(
                    message='Data tidak valid',
                    errors=serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat membuat kendaraan bermotor',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class KendaraanBermotorDetailView(APIView):
    """
    API endpoint untuk detail, update, dan delete KendaraanBermotor
    GET: Get detail kendaraan bermotor
    PUT: Update kendaraan bermotor
    PATCH: Partial update kendaraan bermotor
    DELETE: Delete kendaraan bermotor
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get_object(self, pk):
        """
        Helper method untuk get object atau raise 404
        """
        try:
            return KendaraanBermotor.objects.select_related(
                'jenis', 'merek', 'type_kendaraan', 'wajib_pajak'
            ).get(pk=pk)
        except KendaraanBermotor.DoesNotExist:
            return None
    
    def get(self, request, pk):
        """
        Get detail kendaraan bermotor
        """
        try:
            kendaraan = self.get_object(pk)
            
            if not kendaraan:
                return APIResponse.error(
                    message='Kendaraan bermotor tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            serializer = KendaraanBermotorSerializer(kendaraan)
            return APIResponse.success(
                data=serializer.data,
                message='Data kendaraan bermotor berhasil diambil'
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengambil data kendaraan bermotor',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def put(self, request, pk):
        """
        Update lengkap kendaraan bermotor
        """
        try:
            kendaraan = self.get_object(pk)
            
            if not kendaraan:
                return APIResponse.error(
                    message='Kendaraan bermotor tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            serializer = KendaraanBermotorSerializer(kendaraan, data=request.data)
            
            if serializer.is_valid():
                kendaraan = serializer.save()
                return APIResponse.success(
                    data=KendaraanBermotorSerializer(kendaraan).data,
                    message='Kendaraan bermotor berhasil diupdate'
                )
            else:
                return APIResponse.error(
                    message='Data tidak valid',
                    errors=serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengupdate kendaraan bermotor',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def patch(self, request, pk):
        """
        Partial update kendaraan bermotor
        """
        try:
            kendaraan = self.get_object(pk)
            
            if not kendaraan:
                return APIResponse.error(
                    message='Kendaraan bermotor tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            serializer = KendaraanBermotorSerializer(kendaraan, data=request.data, partial=True)
            
            if serializer.is_valid():
                kendaraan = serializer.save()
                return APIResponse.success(
                    data=KendaraanBermotorSerializer(kendaraan).data,
                    message='Kendaraan bermotor berhasil diupdate'
                )
            else:
                return APIResponse.error(
                    message='Data tidak valid',
                    errors=serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengupdate kendaraan bermotor',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, pk):
        """
        Delete kendaraan bermotor
        """
        try:
            kendaraan = self.get_object(pk)
            
            if not kendaraan:
                return APIResponse.error(
                    message='Kendaraan bermotor tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Cek apakah kendaraan memiliki transaksi pajak
            from crud.models import TransaksiPajak
            transaksi_count = TransaksiPajak.objects.filter(kendaraan=kendaraan).count()
            
            if transaksi_count > 0:
                return APIResponse.error(
                    message=f'Kendaraan bermotor tidak dapat dihapus karena masih memiliki {transaksi_count} transaksi pajak',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            no_polisi = kendaraan.no_polisi
            kendaraan.delete()
            
            return APIResponse.success(
                data=None,
                message=f'Kendaraan bermotor dengan nomor polisi "{no_polisi}" berhasil dihapus',
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat menghapus kendaraan bermotor',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
