from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.paginator import Paginator

from crud.models import MerekKendaraan
from crud.serializers.merek_kendaraan_serializer import MerekKendaraanSerializer
from crud.utils.response import APIResponse
from crud.utils.permissions import IsAdmin


class MerekKendaraanListView(APIView):
    """
    API endpoint untuk list dan create MerekKendaraan
    GET: List semua merek kendaraan (dengan pagination dan search)
    POST: Create merek kendaraan baru
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        """
        Get list semua merek kendaraan dengan pagination dan search
        """
        try:
            # Get query parameters
            page = request.query_params.get('page', 1)
            page_size = request.query_params.get('page_size', 10)
            search = request.query_params.get('search', '')
            
            # Query base
            queryset = MerekKendaraan.objects.all()
            
            # Filter by search (nama)
            if search:
                queryset = queryset.filter(nama__icontains=search)
            
            # Ordering
            queryset = queryset.order_by('nama')
            
            # Pagination
            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page)
            
            # Serialize data
            serializer = MerekKendaraanSerializer(page_obj, many=True)
            
            # Response dengan pagination info
            return APIResponse.paginated_success(
                data=serializer.data,
                message='Data merek kendaraan berhasil diambil',
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
                message='Terjadi kesalahan saat mengambil data merek kendaraan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """
        Create merek kendaraan baru
        """
        try:
            serializer = MerekKendaraanSerializer(data=request.data)
            
            if serializer.is_valid():
                merek_kendaraan = serializer.save()
                return APIResponse.success(
                    data=MerekKendaraanSerializer(merek_kendaraan).data,
                    message='Merek kendaraan berhasil dibuat',
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
                message='Terjadi kesalahan saat membuat merek kendaraan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MerekKendaraanDetailView(APIView):
    """
    API endpoint untuk detail, update, dan delete MerekKendaraan
    GET: Get detail merek kendaraan
    PUT: Update merek kendaraan
    PATCH: Partial update merek kendaraan
    DELETE: Delete merek kendaraan
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get_object(self, pk):
        """
        Helper method untuk get object atau raise 404
        """
        try:
            return MerekKendaraan.objects.get(pk=pk)
        except MerekKendaraan.DoesNotExist:
            return None
    
    def get(self, request, pk):
        """
        Get detail merek kendaraan
        """
        try:
            merek_kendaraan = self.get_object(pk)
            
            if not merek_kendaraan:
                return APIResponse.error(
                    message='Merek kendaraan tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            serializer = MerekKendaraanSerializer(merek_kendaraan)
            return APIResponse.success(
                data=serializer.data,
                message='Data merek kendaraan berhasil diambil'
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengambil data merek kendaraan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def put(self, request, pk):
        """
        Update lengkap merek kendaraan
        """
        try:
            merek_kendaraan = self.get_object(pk)
            
            if not merek_kendaraan:
                return APIResponse.error(
                    message='Merek kendaraan tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            serializer = MerekKendaraanSerializer(merek_kendaraan, data=request.data)
            
            if serializer.is_valid():
                merek_kendaraan = serializer.save()
                return APIResponse.success(
                    data=MerekKendaraanSerializer(merek_kendaraan).data,
                    message='Merek kendaraan berhasil diupdate'
                )
            else:
                return APIResponse.error(
                    message='Data tidak valid',
                    errors=serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengupdate merek kendaraan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def patch(self, request, pk):
        """
        Partial update merek kendaraan
        """
        try:
            merek_kendaraan = self.get_object(pk)
            
            if not merek_kendaraan:
                return APIResponse.error(
                    message='Merek kendaraan tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            serializer = MerekKendaraanSerializer(merek_kendaraan, data=request.data, partial=True)
            
            if serializer.is_valid():
                merek_kendaraan = serializer.save()
                return APIResponse.success(
                    data=MerekKendaraanSerializer(merek_kendaraan).data,
                    message='Merek kendaraan berhasil diupdate'
                )
            else:
                return APIResponse.error(
                    message='Data tidak valid',
                    errors=serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengupdate merek kendaraan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, pk):
        """
        Delete merek kendaraan
        """
        try:
            merek_kendaraan = self.get_object(pk)
            
            if not merek_kendaraan:
                return APIResponse.error(
                    message='Merek kendaraan tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Cek apakah merek digunakan oleh type kendaraan
            from crud.models import TypeKendaraan
            type_count = TypeKendaraan.objects.filter(merek=merek_kendaraan).count()
            
            if type_count > 0:
                return APIResponse.error(
                    message=f'Merek kendaraan tidak dapat dihapus karena masih memiliki {type_count} type kendaraan',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Cek apakah merek digunakan oleh kendaraan (melalui type_kendaraan)
            from crud.models import KendaraanBermotor
            kendaraan_count = KendaraanBermotor.objects.filter(type_kendaraan__merek=merek_kendaraan).count()
            
            if kendaraan_count > 0:
                return APIResponse.error(
                    message=f'Merek kendaraan tidak dapat dihapus karena masih digunakan oleh {kendaraan_count} kendaraan',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            nama = merek_kendaraan.nama
            merek_kendaraan.delete()
            
            return APIResponse.success(
                data=None,
                message=f'Merek kendaraan "{nama}" berhasil dihapus',
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat menghapus merek kendaraan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

