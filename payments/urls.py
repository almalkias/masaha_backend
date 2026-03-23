from django.urls import path
from .views import CreatePaymentIntentAPIView, VerifyPaymentAPIView

urlpatterns = [
    path("intent/", CreatePaymentIntentAPIView.as_view()),
    path("verify/", VerifyPaymentAPIView.as_view()),
]
