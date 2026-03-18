from django.urls import path
from .views import CheckoutAPIView, OrderListAPIView

urlpatterns = [
    path("checkout/", CheckoutAPIView.as_view()),
    path("", OrderListAPIView.as_view()),
]
