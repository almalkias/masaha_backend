from django.urls import path
from .views.stripe import StripeWebhookAPIView

urlpatterns = [
    path("stripe/", StripeWebhookAPIView.as_view()),
]
