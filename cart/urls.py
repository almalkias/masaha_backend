from django.urls import path
from .views import AddToCartAPIView, CartAPIView, ClearCartAPIView, RemoveFromCartAPIView, UpdateCartItemAPIView

urlpatterns = [
    path("", CartAPIView.as_view()),
    path("add/", AddToCartAPIView.as_view()),
    path("clear/", ClearCartAPIView.as_view()),
    path("<int:item_id>/delete/", RemoveFromCartAPIView.as_view()),
    path("<int:item_id>/update/", UpdateCartItemAPIView.as_view()),
]
