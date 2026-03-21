from django.urls import path
from .views import ChangePasswordAPIView, LogoutAPIView, RegisterAPIView, ProfileAPIView, CustomTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', RegisterAPIView.as_view()),
    path('login/', CustomTokenObtainPairView.as_view()),
    path('profile/', ProfileAPIView.as_view()),
    path('logout/', LogoutAPIView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
    path("change-password/", ChangePasswordAPIView.as_view()),
]
