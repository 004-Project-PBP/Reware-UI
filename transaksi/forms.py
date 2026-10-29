from django import forms
from django.utils import timezone
from .models import TransaksiCOD, TitikCOD, Ulasan
from django.utils.html import strip_tags  #Sanitization for user input to prevent XSS attacks

class PengajuanBeliForm(forms.ModelForm):
    class Meta:
        model = TransaksiCOD
        fields = ['titik_cod','jadwal_temu', 'catatan_buyer']
        widgets={
            'titik_cod': forms.Select(attrs={
                'class':'form-control',
                'id': 'select-titik-cod'
            }),
            'jadwal_temu': forms.DateTimeInput(attrs={
                'type':'datetime-local',
                'class':'form-control'
            }),
            'catatan_buyer': forms.Textarea(attrs={
                'rows':3,
                'class': 'form-control',
                'placeholder':'Cth: Saya pakai jacket kuning, hubungi saya di 081234...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args,**kwargs)
        self.fields ['titik_cod'].queryset= TitikCOD.objects.filter(is_active=True)

    def clean_jadwal_temu(self):
        jadwal = self.cleaned_data.get('jadwal_temu')
        if jadwal and jadwal <= timezone.now():
            raise forms.ValidationError("Jadwal temu harus ada di waktu berdatang")
        return jadwal
    def clean_catatan_buyer(self):
        catatan = self.cleaned_data.get('catatan_buyer', '')
        return strip_tags(catatan)

class UlasanForm(forms.ModelForm):
    class Meta:
        model = Ulasan
        fields = ['rating', 'komentar']
        widget={
            'rating':forms.NumberInput(attrs={
                'class':'form-control',
                'min':1,
                'max':5
            }),
            'komentar':forms.Textarea(attrs={
                'rows':3,
                'class': 'form-control',
                'placeholder':'Tulis ulasan singkat mengenai transaksi COD ini. Cth: Sangat bagus, cakep pen...'
            }),
        }
    def clean_komentar(self):
        komentar = self.cleaned_data.get('komentar', '')
        return strip_tags(komentar)
