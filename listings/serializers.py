from rest_framework import serializers

from .models import Listing


class ListingSerializer(serializers.ModelSerializer):
    seller = serializers.ReadOnlyField(source="seller.username")
    brand_name = serializers.ReadOnlyField(source="brand.name")
    category_name = serializers.ReadOnlyField(source="category.name")
    condition_label = serializers.CharField(source="get_condition_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    savings_percent = serializers.ReadOnlyField()

    class Meta:
        model = Listing
        fields = [
            "id", "seller", "title", "description", "photo",
            "brand", "brand_name", "category", "category_name",
            "size", "condition", "condition_label",
            "price", "retail_price", "savings_percent",
            "stock", "cod_point", "status", "status_label", "created_at",
        ]
        read_only_fields = ["seller", "created_at"]