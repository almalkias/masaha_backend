from django.urls import path
from .views import OrderListAPIView

urlpatterns = [
    path("", OrderListAPIView.as_view()),
]
