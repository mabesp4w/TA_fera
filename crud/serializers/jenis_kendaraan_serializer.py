from rest_framework import serializers
from crud.models import JenisKendaraan


class JenisKendaraanSerializer(serializers.ModelSerializer):
    """
    Serializer untuk JenisKendaraan
    """
    kategori_display = serializers.CharField(source='get_kategori_display', read_only=True)
    
    class Meta:
        model = JenisKendaraan
        fields = ['id', 'nama', 'kategori', 'kategori_display']
        read_only_fields = ['id']
    
    def validate_nama(self, value):
        """
        Validasi nama harus unik
        """
        # Cek apakah nama sudah ada (kecuali untuk instance yang sedang diupdate)
        instance = self.instance
        if instance:
            # Update: cek duplikat kecuali instance sendiri
            if JenisKendaraan.objects.filter(nama=value).exclude(pk=instance.pk).exists():
                raise serializers.ValidationError("Nama jenis kendaraan sudah ada.")
        else:
            # Create: cek duplikat
            if JenisKendaraan.objects.filter(nama=value).exists():
                raise serializers.ValidationError("Nama jenis kendaraan sudah ada.")
        return value
    
    def validate_kategori(self, value):
        """
        Validasi kategori harus valid
        """
        valid_categories = ['MOTOR', 'MOBIL', 'JEEP', 'TRUK', 'BUS', 'LAINNYA']
        if value not in valid_categories:
            raise serializers.ValidationError(
                f"Kategori harus salah satu dari: {', '.join(valid_categories)}"
            )
        return value

