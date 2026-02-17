from rest_framework import serializers
from crud.models import WajibPajak, Kelurahan


class WajibPajakSerializer(serializers.ModelSerializer):
    """
    Serializer untuk WajibPajak
    """
    kelurahan_nama = serializers.SerializerMethodField()
    kecamatan_nama = serializers.SerializerMethodField()
    
    class Meta:
        model = WajibPajak
        fields = [
            'id', 'no_ktp', 'nama', 'alamat', 
            'kelurahan', 'kelurahan_nama', 'kecamatan_nama',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'kelurahan_nama', 'kecamatan_nama']
    
    def get_kelurahan_nama(self, obj):
        """Get nama kelurahan"""
        if obj.kelurahan:
            return obj.kelurahan.nama
        return None
    
    def get_kecamatan_nama(self, obj):
        """Get nama kecamatan dari kelurahan"""
        if obj.kelurahan and obj.kelurahan.kecamatan:
            return obj.kelurahan.kecamatan.nama
        return None
    
    def validate_no_ktp(self, value):
        """
        Validasi no_ktp harus unik jika diisi
        """
        if value:
            instance = self.instance
            if instance:
                # Update: cek duplikat kecuali instance sendiri
                if WajibPajak.objects.filter(no_ktp=value).exclude(pk=instance.pk).exists():
                    raise serializers.ValidationError("Nomor KTP sudah terdaftar.")
            else:
                # Create: cek duplikat
                if WajibPajak.objects.filter(no_ktp=value).exists():
                    raise serializers.ValidationError("Nomor KTP sudah terdaftar.")
        return value
    
    def validate_kelurahan(self, value):
        """
        Validasi kelurahan harus ada jika diisi
        """
        if value:
            # Cek apakah kelurahan ada di database
            if not Kelurahan.objects.filter(pk=value.pk).exists():
                raise serializers.ValidationError("Kelurahan tidak ditemukan.")
        return value

