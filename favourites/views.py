from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from products.models import Product
from products.serializers import ProductSerializer
from .models import Favourite


# Return the favorited products directly
class FavouriteListAPIView(ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Product.objects.filter(
            favourited_by__user=self.request.user
        )


# Add or remove a favorite entry
class FavouriteToggleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id, is_active=True)
        Favourite.objects.get_or_create(user=request.user, product=product)
        return Response({"status": "added"}, status=status.HTTP_201_CREATED)

    def delete(self, request, product_id):
        Favourite.objects.filter(
            user=request.user,
            product_id=product_id
        ).delete()
        return Response({"status": "removed"})
    
