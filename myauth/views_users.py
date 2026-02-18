from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from crud.utils.response import APIResponse
from myauth.models import User
from myauth.serializers.user_serializer import (
    UserListSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer
)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class UserListView(APIView):
    """
    API endpoint untuk list dan create users
    GET: List users dengan pagination dan filter
    POST: Create user baru
    """
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get(self, request):
        # Filter params
        search = request.query_params.get('search', '')
        role = request.query_params.get('role', '')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        
        # Queryset
        queryset = User.objects.all().order_by('-id')
        
        # Filter by search
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        # Filter by role
        if role:
            queryset = queryset.filter(role=role)
        
        # Pagination
        paginator = self.pagination_class()
        paginator.page_size = page_size
        result_page = paginator.paginate_queryset(queryset, request)
        
        serializer = UserListSerializer(result_page, many=True)
        
        response_data = {
            'data': serializer.data,
            'total_count': queryset.count(),
            'total_pages': paginator.page.paginator.num_pages if hasattr(paginator, 'page') else 1,
            'page': page,
            'page_size': page_size,
        }
        
        return APIResponse.success(
            data=response_data,
            message='Data pengguna berhasil diambil'
        )
    
    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            return APIResponse.success(
                data=UserListSerializer(user).data,
                message='Pengguna berhasil ditambahkan',
                status_code=status.HTTP_201_CREATED
            )
        
        return APIResponse.error(
            message='Validasi gagal',
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class UserDetailView(APIView):
    """
    API endpoint untuk detail, update, dan delete user
    GET: Get user detail
    PATCH: Update user
    DELETE: Delete user
    """
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            return None
    
    def get(self, request, pk):
        user = self.get_object(pk)
        if not user:
            return APIResponse.error(
                message='Pengguna tidak ditemukan',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        serializer = UserListSerializer(user)
        return APIResponse.success(
            data=serializer.data,
            message='Data pengguna berhasil diambil'
        )
    
    def patch(self, request, pk):
        user = self.get_object(pk)
        if not user:
            return APIResponse.error(
                message='Pengguna tidak ditemukan',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            user = serializer.save()
            return APIResponse.success(
                data=UserListSerializer(user).data,
                message='Pengguna berhasil diperbarui'
            )
        
        return APIResponse.error(
            message='Validasi gagal',
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    def delete(self, request, pk):
        user = self.get_object(pk)
        if not user:
            return APIResponse.error(
                message='Pengguna tidak ditemukan',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Prevent delete self
        if user.id == request.user.id:
            return APIResponse.error(
                message='Tidak dapat menghapus akun sendiri',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        user.delete()
        return APIResponse.success(
            message='Pengguna berhasil dihapus'
        )


class ChangePasswordView(APIView):
    """
    API endpoint untuk reset password (admin only)
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return APIResponse.error(
                message='Pengguna tidak ditemukan',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ChangePasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            password = serializer.validated_data['password']
            user.set_password(password)
            user.show_password = password
            user.save()
            
            return APIResponse.success(
                message='Password berhasil diubah'
            )
        
        return APIResponse.error(
            message='Validasi gagal',
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class UsersByRoleView(APIView):
    """
    API endpoint untuk mendapatkan users berdasarkan role
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        role = request.query_params.get('role', '')
        
        if not role:
            return APIResponse.error(
                message='Parameter role wajib diisi',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        users = User.objects.filter(role=role)
        serializer = UserListSerializer(users, many=True)
        
        return APIResponse.success(
            data=serializer.data,
            message='Data pengguna berhasil diambil'
        )
