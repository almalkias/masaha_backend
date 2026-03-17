from django.urls import path
from .views import ProductListAPIView, ProductDetailAPIView

urlpatterns = [
    path("", ProductListAPIView.as_view(), name="product-list"),
    path("<int:pk>/", ProductDetailAPIView.as_view(), name="product-detail"),
]
