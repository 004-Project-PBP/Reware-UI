from rest_framework import serializers
from .models import TitikCOD, TransaksiCOD, Ulasan

class TitikCODSerializer(serializers.ModelSerializer):
    class Meta:
        model = TitikCOD
        fields = '__all__'

class TransaksiCODSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransaksiCOD
        fields = '__all__'

class UlasanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ulasan
        fields = '__all__'