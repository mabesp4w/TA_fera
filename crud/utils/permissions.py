from rest_framework import permissions
from myauth.models import User


class IsAdmin(permissions.BasePermission):
    """
    Permission class untuk memastikan hanya admin yang bisa akses
    """
    message = 'Hanya admin yang dapat mengakses endpoint ini.'

    def has_permission(self, request, view):
        # Cek apakah user sudah login
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Cek apakah user adalah admin (berdasarkan role atau is_superuser)
        return (
            request.user.role == 'admin' or 
            request.user.is_superuser or 
            request.user.is_staff
        )

