from django import forms
from .models import Listing


class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = [
            "title", "description", "photo", "size",
            "condition", "price", "retail_price", "stock", "cod_point",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "cth. Uniqlo Oversized Tee — Like New"}),
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": "Deskripsikan kondisi barang yang jujur"}),
            "size": forms.RadioSelect,
            "condition": forms.RadioSelect,
            "price": forms.TextInput(attrs={"placeholder": "Rp 0", "inputmode": "numeric", "autocomplete": "off"}),
            "retail_price": forms.TextInput(attrs={"placeholder": "cth. 299.000", "inputmode": "numeric", "autocomplete": "off"}),
            "stock": forms.NumberInput(attrs={"min": 1}),
            "cod_point": forms.TextInput(attrs={"placeholder": "cth. Stasiun UI"}),
        }
        labels = {
            "retail_price": "Harga ritel acuan (sementara)",
            "cod_point": "Titik COD",
        }

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price <= 0:
            raise forms.ValidationError("Harga harus lebih dari 0.")
        return price