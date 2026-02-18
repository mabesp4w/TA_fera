from django.urls import path
from .views import LoginView, LogoutView, UserProfileView
from .views_users import UserListView, UserDetailView, ChangePasswordView, UsersByRoleView

app_name = 'myauth'

urlpatterns = [
    # Auth endpoints
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    
    # User management endpoints
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('users/<int:pk>/change-password/', ChangePasswordView.as_view(), name='user-change-password'),
    path('users/by-role/', UsersByRoleView.as_view(), name='users-by-role'),
]

