from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DashboardView,
)

router = DefaultRouter()

app_name = 'crud'

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    ]