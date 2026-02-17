from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Custom User model dengan field tambahan role dan show_password
    """
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('user', 'User'),
        ('staff', 'Staff'),
    ]
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='user',
        help_text='Role pengguna dalam sistem'
    )
    
    show_password = models.CharField(
        max_length=50,
        help_text='Menampilkan password di UI (untuk keperluan admin)'
    )
    
    class Meta:
        db_table = 'auth_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return self.username

