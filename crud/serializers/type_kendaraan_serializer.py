from rest_framework import serializers
from crud.models import TypeKendaraan, MerekKendaraan


class TypeKendaraanSerializer(serializers.ModelSerializer):
    """
    Serializer untuk TypeKendaraan
    """
    merek_nama = serializers.CharField(source='merek.nama', read_only=True)
    
    class Meta:
        model = TypeKendaraan
        fields = ['id', 'nama', 'merek', 'merek_nama']
        read_only_fields = ['id', 'merek_nama']
    
    def validate(self, attrs):
        """
        Validasi kombinasi merek dan nama harus unik
        """
        merek = attrs.get('merek')
        nama = attrs.get('nama')
        instance = self.instance
        
        if merek and nama:
            # Cek apakah kombinasi merek + nama sudah ada
            queryset = TypeKendaraan.objects.filter(merek=merek, nama=nama)
            
            if instance:
                # Update: cek duplikat kecuali instance sendiri
                queryset = queryset.exclude(pk=instance.pk)
            
            if queryset.exists():
                raise serializers.ValidationError(
                    f"Type kendaraan dengan nama '{nama}' sudah ada untuk merek '{merek.nama}'."
                )
        
        return attrs
    
    def validate_merek(self, value):
        """
        Validasi merek harus ada
        """
        if not value:
            raise serializers.ValidationError("Merek kendaraan harus dipilih.")
        
        # Cek apakah merek ada di database
        if not MerekKendaraan.objects.filter(pk=value.pk).exists():
            raise serializers.ValidationError("Merek kendaraan tidak ditemukan.")
        
        return value

