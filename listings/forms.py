from django import forms

from main.models import Brand, Category

from .models import Listing


class BrandSelect(forms.Select):
    """Select brand yang nyimpen range harga ritel di tiap option (buat live Hemat %)."""

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        brand = getattr(value, "instance", None)
        if brand:
            option["attrs"]["data-min"] = brand.retail_price_min
            option["attrs"]["data-max"] = brand.retail_price_max
        return option


class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = [
            "title", "description", "photo", "brand", "category", "size",
            "condition", "price", "retail_price", "stock", "cod_point",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "cth. Uniqlo Oversized Tee — Like New"}),
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": "Deskripsikan kondisi barang yang jujur"}),
            "brand": BrandSelect,
            "size": forms.RadioSelect,
            "condition": forms.RadioSelect,
            "price": forms.TextInput(attrs={"placeholder": "Rp 0", "inputmode": "numeric", "autocomplete": "off"}),
            "retail_price": forms.TextInput(attrs={"placeholder": "cth. 299.000", "inputmode": "numeric", "autocomplete": "off"}),
            "stock": forms.NumberInput(attrs={"min": 1}),
            "cod_point": forms.TextInput(attrs={"placeholder": "cth. Stasiun UI"}),
        }
        labels = {
            "retail_price": "Harga ritel acuan",
            "cod_point": "Titik COD",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["brand"].queryset = Brand.objects.order_by("name")
        self.fields["brand"].empty_label = "Pilih brand…"
        self.fields["category"].queryset = Category.objects.order_by("name")
        self.fields["category"].empty_label = "Pilih kategori…"

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price <= 0:
            raise forms.ValidationError("Harga harus lebih dari 0.")
        return price