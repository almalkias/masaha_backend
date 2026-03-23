from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView

from .models import Product
from .serializers import ProductSerializer

    
class ProductListAPIView(ListAPIView):
    queryset = Product.objects.filter(is_active=True, stock__gt=0)
    serializer_class = ProductSerializer

    def get_serializer_context(self):
        return {"request": self.request}


class ProductDetailAPIView(APIView):
    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk, is_active=True)

        serializer = ProductSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)
    