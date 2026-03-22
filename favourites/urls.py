from django.urls import path
from .views import FavouriteListAPIView, FavouriteToggleAPIView

urlpatterns = [
    path("", FavouriteListAPIView.as_view()),
    path("<int:product_id>/", FavouriteToggleAPIView.as_view()),
]
