from django.urls import path
from .views import CreatePaymentIntentAPIView

urlpatterns = [
    path("intent/", CreatePaymentIntentAPIView.as_view()),
]
