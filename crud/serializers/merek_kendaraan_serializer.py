from rest_framework import serializers
from crud.models import MerekKendaraan


class MerekKendaraanSerializer(serializers.ModelSerializer):
    """
    Serializer untuk MerekKendaraan
    """
    class Meta:
        model = MerekKendaraan
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
            if MerekKendaraan.objects.filter(nama=value).exclude(pk=instance.pk).exists():
                raise serializers.ValidationError("Nama merek kendaraan sudah ada.")
        else:
            # Create: cek duplikat
            if MerekKendaraan.objects.filter(nama=value).exists():
                raise serializers.ValidationError("Nama merek kendaraan sudah ada.")
        return value

