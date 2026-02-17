from rest_framework import serializers
from crud.models import Kecamatan


class KecamatanSerializer(serializers.ModelSerializer):
    """
    Serializer untuk Kecamatan
    """
    class Meta:
        model = Kecamatan
        fields = ['id', 'nama']
        read_only_fields = ['id']
    
    def validate_nama(self, value):
        """
        Validasi nama harus unik
        """
        # Cek apakah nama sudah ada (kecuali untuk instance yang sedang diupdate)
        instance = self.instance
        if instance:
            # Update: cek duplikat kecuali instance sendiri
            if Kecamatan.objects.filter(nama=value).exclude(pk=instance.pk).exists():
                raise serializers.ValidationError("Nama kecamatan sudah ada.")
        else:
            # Create: cek duplikat
            if Kecamatan.objects.filter(nama=value).exists():
                raise serializers.ValidationError("Nama kecamatan sudah ada.")
        return value

