from django.urls import path
from .views import ValidateCouponAPIView

urlpatterns = [
    path("validate/", ValidateCouponAPIView.as_view()),
]
