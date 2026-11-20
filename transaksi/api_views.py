from rest_framework import viewsets
from .models import TitikCOD, TransaksiCOD, Ulasan
from .serializers import TitikCODSerializer, TransaksiCODSerializer, UlasanSerializer

class TitikCODViewSet(viewsets.ModelViewSet):
    queryset = TitikCOD.objects.all()
    serializer_class = TitikCODSerializer

class TransaksiCODViewSet(viewsets.ModelViewSet):
    queryset = TransaksiCOD.objects.all()
    serializer_class = TransaksiCODSerializer

class UlasanViewSet(viewsets.ModelViewSet):
    queryset = Ulasan.objects.all()
    serializer_class = UlasanSerializer