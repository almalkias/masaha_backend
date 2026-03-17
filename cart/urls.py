from django.urls import path
from .views import AddToCartAPIView, CartAPIView, RemoveFromCartAPIView, UpdateCartItemAPIView

urlpatterns = [
    path("add/", AddToCartAPIView.as_view()),
    path("", CartAPIView.as_view()),
    path("<int:item_id>/", RemoveFromCartAPIView.as_view()),
    path("items/<int:item_id>/update/", UpdateCartItemAPIView.as_view()),
]
