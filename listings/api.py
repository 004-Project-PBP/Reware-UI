from django.db.models import Q
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Listing
from .serializers import ListingSerializer


class IsSellerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.seller_id == request.user.id


class ListingViewSet(viewsets.ModelViewSet):
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsSellerOrReadOnly]

    def get_queryset(self):
        qs = Listing.objects.select_related("seller", "brand", "category").order_by("-created_at")
        user = self.request.user
        if user.is_authenticated:
            qs = qs.filter(~Q(status="archived") | Q(seller=user))
        else:
            qs = qs.exclude(status="archived")

        params = self.request.query_params
        if params.get("brand"):
            qs = qs.filter(brand_id=params["brand"])
        if params.get("category"):
            qs = qs.filter(category_id=params["category"])
        if params.get("status"):
            qs = qs.filter(status=params["status"])
        return qs

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def mine(self, request):
        qs = self.get_queryset().filter(seller=request.user)
        return Response(self.get_serializer(qs, many=True).data)

    @action(detail=True, methods=["post"], url_path="status")
    def set_status(self, request, pk=None):
        listing = self.get_object()
        new_status = request.data.get("status")
        if new_status not in Listing.Status.values:
            return Response({"detail": "Status tidak valid."}, status=400)
        listing.status = new_status
        listing.save(update_fields=["status"])
        return Response(self.get_serializer(listing).data)