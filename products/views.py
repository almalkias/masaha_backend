from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import Product
from .serializers import ProductSerializer


class ProductListAPIView(APIView):
    def get(self, request):
        products = Product.objects.filter(is_active=True)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductDetailAPIView(APIView):
    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk, is_active=True)

        serializer = ProductSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)
    