from django import forms
from .models import Brand, Category

# Add forms here

class BrandProposalForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        required=True,
        label="Kategori Pakaian"
    )

    class Meta:
        model = Brand
        # Only include modifyable fields
        fields = ['name', 'logo_url', 'brand_type', 'categories', 'retail_price_min', 'retail_price_max']
        labels = {
            'name': 'Nama Brand',
            'logo_url': 'URL Logo Brand (Opsional)',
            'brand_type': 'Tipe Brand',
            'retail_price_min': 'Harga Ritel Minimum (Rp)',
            'retail_price_max': 'Harga Ritel Maksimum (Rp)',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'filter-input',
                'placeholder': 'Contoh: Uniqlo, Erigo, Zara...',
                'style': 'width: 100%;'
            }),
            'logo_url': forms.URLInput(attrs={
                'class': 'filter-input',
                'placeholder': 'https://example.com/logo.png',
                'style': 'width: 100%;'
            }),
            'brand_type': forms.Select(attrs={
                'class': 'filter-select',
                'style': 'width: 100%;'
            }),
            'retail_price_min': forms.NumberInput(attrs={
                'class': 'filter-input',
                'placeholder': '100000',
                'min': '0',
                'style': 'width: 100%;'
            }),
            'retail_price_max': forms.NumberInput(attrs={
                'class': 'filter-input',
                'placeholder': '500000',
                'min': '0',
                'style': 'width: 100%;'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        min_price = cleaned_data.get('retail_price_min')
        max_price = cleaned_data.get('retail_price_max')

        # Validate that maximum price is >= minimum price
        if min_price is not None and max_price is not None and min_price > max_price:
            raise forms.ValidationError(
                "Harga ritel maksimum harus lebih besar atau sama dengan harga ritel minimum."
            )
        return cleaned_data

class BrandEditForm(BrandProposalForm):
    # Inherit same fields and style to make it simple :p
    pass