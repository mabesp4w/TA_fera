from rest_framework import serializers
from django.contrib.auth import authenticate
from myauth.models import User


class LoginSerializer(serializers.Serializer):
    """
    Serializer untuk login
    """
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError(
                    'Username atau password salah.',
                    code='authorization'
                )
            if not user.is_active:
                raise serializers.ValidationError(
                    'Akun pengguna dinonaktifkan.',
                    code='authorization'
                )
            attrs['user'] = user
        else:
            raise serializers.ValidationError(
                'Username dan password harus diisi.',
                code='authorization'
            )

        return attrs


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer untuk data user
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role']
        read_only_fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role']

