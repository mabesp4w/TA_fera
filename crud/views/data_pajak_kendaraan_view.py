from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.paginator import Paginator
from django.db.models import Q

from crud.models import DataPajakKendaraan
from crud.serializers.data_pajak_kendaraan_serializer import DataPajakKendaraanSerializer
from crud.utils.response import APIResponse
from crud.utils.permissions import IsAdmin


class DataPajakKendaraanListView(APIView):
    """
    API endpoint untuk list dan create DataPajakKendaraan
    GET: List semua data pajak kendaraan (dengan pagination dan search)
    POST: Create data pajak kendaraan baru
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        """
        Get list semua data pajak kendaraan dengan pagination dan search
        """
        try:
            # Get query parameters
            page = request.query_params.get('page', 1)
            page_size = request.query_params.get('page_size', 10)
            search = request.query_params.get('search', '')
            kendaraan_id = request.query_params.get('kendaraan_id', '')
            no_polisi = request.query_params.get('no_polisi', '')
            
            # Query base dengan select_related untuk optimasi
            queryset = DataPajakKendaraan.objects.select_related(
                'kendaraan__merek', 'kendaraan__type_kendaraan'
            ).all()
            
            # Filter by search (no_polisi kendaraan)
            if search:
                queryset = queryset.filter(
                    Q(kendaraan__no_polisi__icontains=search) |
                    Q(kendaraan__merek__nama__icontains=search) |
                    Q(kendaraan__type_kendaraan__nama__icontains=search)
                )
            
            # Filter by kendaraan_id
            if kendaraan_id:
                queryset = queryset.filter(kendaraan_id=kendaraan_id)
            
            # Filter by no_polisi
            if no_polisi:
                queryset = queryset.filter(kendaraan__no_polisi__icontains=no_polisi)
            
            # Ordering
            queryset = queryset.order_by('-updated_at', 'kendaraan__no_polisi')
            
            # Pagination
            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page)
            
            # Serialize data
            serializer = DataPajakKendaraanSerializer(page_obj, many=True)
            
            # Response dengan pagination info
            return APIResponse.paginated_success(
                data=serializer.data,
                message='Data pajak kendaraan berhasil diambil',
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
                message='Terjadi kesalahan saat mengambil data pajak kendaraan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """
        Create data pajak kendaraan baru
        """
        try:
            serializer = DataPajakKendaraanSerializer(data=request.data)
            
            if serializer.is_valid():
                data_pajak = serializer.save()
                return APIResponse.success(
                    data=DataPajakKendaraanSerializer(data_pajak).data,
                    message='Data pajak kendaraan berhasil dibuat',
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
                message='Terjadi kesalahan saat membuat data pajak kendaraan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DataPajakKendaraanDetailView(APIView):
    """
    API endpoint untuk detail, update, dan delete DataPajakKendaraan
    GET: Get detail data pajak kendaraan
    PUT: Update data pajak kendaraan
    PATCH: Partial update data pajak kendaraan
    DELETE: Delete data pajak kendaraan
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get_object(self, pk):
        """
        Helper method untuk get object atau raise 404
        """
        try:
            return DataPajakKendaraan.objects.select_related(
                'kendaraan__merek', 'kendaraan__type_kendaraan'
            ).get(pk=pk)
        except DataPajakKendaraan.DoesNotExist:
            return None
    
    def get(self, request, pk):
        """
        Get detail data pajak kendaraan
        """
        try:
            data_pajak = self.get_object(pk)
            
            if not data_pajak:
                return APIResponse.error(
                    message='Data pajak kendaraan tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            serializer = DataPajakKendaraanSerializer(data_pajak)
            return APIResponse.success(
                data=serializer.data,
                message='Data pajak kendaraan berhasil diambil'
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengambil data pajak kendaraan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def put(self, request, pk):
        """
        Update lengkap data pajak kendaraan
        """
        try:
            data_pajak = self.get_object(pk)
            
            if not data_pajak:
                return APIResponse.error(
                    message='Data pajak kendaraan tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            serializer = DataPajakKendaraanSerializer(data_pajak, data=request.data)
            
            if serializer.is_valid():
                data_pajak = serializer.save()
                return APIResponse.success(
                    data=DataPajakKendaraanSerializer(data_pajak).data,
                    message='Data pajak kendaraan berhasil diupdate'
                )
            else:
                return APIResponse.error(
                    message='Data tidak valid',
                    errors=serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengupdate data pajak kendaraan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def patch(self, request, pk):
        """
        Partial update data pajak kendaraan
        """
        try:
            data_pajak = self.get_object(pk)
            
            if not data_pajak:
                return APIResponse.error(
                    message='Data pajak kendaraan tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            serializer = DataPajakKendaraanSerializer(data_pajak, data=request.data, partial=True)
            
            if serializer.is_valid():
                data_pajak = serializer.save()
                return APIResponse.success(
                    data=DataPajakKendaraanSerializer(data_pajak).data,
                    message='Data pajak kendaraan berhasil diupdate'
                )
            else:
                return APIResponse.error(
                    message='Data tidak valid',
                    errors=serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengupdate data pajak kendaraan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, pk):
        """
        Delete data pajak kendaraan
        """
        try:
            data_pajak = self.get_object(pk)
            
            if not data_pajak:
                return APIResponse.error(
                    message='Data pajak kendaraan tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            no_polisi = data_pajak.kendaraan.no_polisi
            data_pajak.delete()
            
            return APIResponse.success(
                data=None,
                message=f'Data pajak kendaraan untuk "{no_polisi}" berhasil dihapus',
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat menghapus data pajak kendaraan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

