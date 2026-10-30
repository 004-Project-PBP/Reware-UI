from django import forms
from .models import Item, Brand, Category

class ItemProposalForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = [
            'name', 
            'brand', 
            'category', 
            'price', 
            'retail_price', 
            'size', 
            'condition', 
            'cod_location', 
            'image'
        ]
        labels = {
            'name': 'Nama Item / Pakaian',
            'brand': 'Brand',
            'category': 'Kategori',
            'price': 'Harga Jual (Rp)',
            'retail_price': 'Harga Ritel Asli (Rp)',
            'size': 'Ukuran',
            'condition': 'Kondisi Barang',
            'cod_location': 'Lokasi COD / Kampus',
            'image': 'Foto Pakaian',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'filter-input', 'placeholder': 'Contoh: Kemeja Linen Oversize'}),
            'brand': forms.Select(attrs={'class': 'filter-select'}),
            'category': forms.Select(attrs={'class': 'filter-select'}),
            'price': forms.NumberInput(attrs={'class': 'filter-input', 'placeholder': '45000'}),
            'retail_price': forms.NumberInput(attrs={'class': 'filter-input', 'placeholder': '150000'}),
            'size': forms.TextInput(attrs={'class': 'filter-select'}),
            'condition': forms.Select(attrs={'class': 'filter-select'}),
            'cod_location': forms.TextInput(attrs={'class': 'filter-select'}),
            'image': forms.ClearableFileInput(attrs={'class': 'filter-input'}),
        }