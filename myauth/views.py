from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from oauth2_provider.models import Application, AccessToken
from oauth2_provider.settings import oauth2_settings
from oauthlib.common import generate_token
from django.utils import timezone
from datetime import timedelta
from crud.utils.response import APIResponse
from .serializers.auth_serializer import LoginSerializer, UserSerializer


class LoginView(APIView):
    """
    API endpoint untuk login dan mendapatkan token
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Dapatkan atau buat OAuth2 Application (gunakan superuser pertama atau buat default)
            try:
                app = Application.objects.filter(
                    client_type=Application.CLIENT_CONFIDENTIAL,
                    authorization_grant_type=Application.GRANT_PASSWORD
                ).first()
                
                if not app:
                    # Buat application default jika belum ada
                    from myauth.models import User as CustomUser
                    admin_user = CustomUser.objects.filter(is_superuser=True).first()
                    if not admin_user:
                        admin_user = user
                    
                    app = Application.objects.create(
                        name='Default Application',
                        client_type=Application.CLIENT_CONFIDENTIAL,
                        authorization_grant_type=Application.GRANT_PASSWORD,
                        user=admin_user,
                    )
            except Exception as e:
                # Fallback: buat application baru
                from myauth.models import User as CustomUser
                admin_user = CustomUser.objects.filter(is_superuser=True).first() or user
                app = Application.objects.create(
                    name='Default Application',
                    client_type=Application.CLIENT_CONFIDENTIAL,
                    authorization_grant_type=Application.GRANT_PASSWORD,
                    user=admin_user,
                )
            
            # Generate access token
            access_token = self._generate_access_token(user, app)
            
            # Serialize user data
            user_data = UserSerializer(user).data
            
            # Response dengan token dan role
            response_data = {
                'token': access_token,
                'role': user.role,
                'user': user_data,
                'expires_in': oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS,
            }
            
            return APIResponse.success(
                data=response_data,
                message='Login berhasil',
                status_code=status.HTTP_200_OK
            )
        
        return APIResponse.error(
            message='Validasi gagal',
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    def _generate_access_token(self, user, application):
        """
        Generate OAuth2 access token untuk user
        """
        # Hapus token lama jika ada
        AccessToken.objects.filter(user=user, application=application).delete()
        
        # Buat token baru
        expires = timezone.now() + timedelta(seconds=oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS)
        token = generate_token()
        
        access_token = AccessToken.objects.create(
            user=user,
            application=application,
            token=token,
            expires=expires,
            scope='read write'
        )
        
        return token


class LogoutView(APIView):
    """
    API endpoint untuk logout (menghapus token)
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        from oauth2_provider.models import AccessToken
        
        # Hapus token user yang sedang login
        AccessToken.objects.filter(user=request.user).delete()
        
        return APIResponse.success(
            message='Logout berhasil',
            status_code=status.HTTP_200_OK
        )


class UserProfileView(APIView):
    """
    API endpoint untuk mendapatkan profile user yang sedang login
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user_data = UserSerializer(request.user).data
        response_data = {
            'role': request.user.role,
            'user': user_data,
        }
        
        return APIResponse.success(
            data=response_data,
            message='Data profile berhasil diambil',
            status_code=status.HTTP_200_OK
        )
