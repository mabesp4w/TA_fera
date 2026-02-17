from rest_framework import serializers
from crud.models import Kelurahan, Kecamatan


class KelurahanSerializer(serializers.ModelSerializer):
    """
    Serializer untuk Kelurahan
    """
    kecamatan_nama = serializers.CharField(source='kecamatan.nama', read_only=True)
    
    class Meta:
        model = Kelurahan
        fields = ['id', 'nama', 'kecamatan', 'kecamatan_nama']
        read_only_fields = ['id', 'kecamatan_nama']
    
    def validate(self, attrs):
        """
        Validasi kombinasi kecamatan dan nama harus unik
        """
        kecamatan = attrs.get('kecamatan')
        nama = attrs.get('nama')
        instance = self.instance
        
        if kecamatan and nama:
            # Cek apakah kombinasi kecamatan + nama sudah ada
            queryset = Kelurahan.objects.filter(kecamatan=kecamatan, nama=nama)
            
            if instance:
                # Update: cek duplikat kecuali instance sendiri
                queryset = queryset.exclude(pk=instance.pk)
            
            if queryset.exists():
                raise serializers.ValidationError(
                    f"Kelurahan dengan nama '{nama}' sudah ada di kecamatan '{kecamatan.nama}'."
                )
        
        return attrs
    
    def validate_kecamatan(self, value):
        """
        Validasi kecamatan harus ada
        """
        if not value:
            raise serializers.ValidationError("Kecamatan harus dipilih.")
        
        # Cek apakah kecamatan ada di database
        if not Kecamatan.objects.filter(pk=value.pk).exists():
            raise serializers.ValidationError("Kecamatan tidak ditemukan.")
        
        return value

