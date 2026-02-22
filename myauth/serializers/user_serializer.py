from rest_framework import serializers
from myauth.models import User


class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer untuk list user (readonly)
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'show_password']


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer untuk create user baru
    """
    password = serializers.CharField(write_only=True, min_length=6)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'password']
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.show_password = password  # Simpan plain password untuk keperluan admin
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer untuk update user
    """
    password = serializers.CharField(write_only=True, min_length=6, required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'password']
        read_only_fields = ['id', 'username']
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        
        # Update fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Update password jika disediakan
        if password:
            instance.set_password(password)
            instance.show_password = password
        
        instance.save()
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer untuk reset password (admin only)
    """
    password = serializers.CharField(min_length=6)
