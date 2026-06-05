from django.utils.translation import gettext_lazy as _
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import (
    ProfileUpdateSerializer,
    RegisterSerializer,
    ProfileSerializer,
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
    ForgotPasswordSerializer,
    ResetPasswordConfirmSerializer,
)


class RegisterAPIView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "message": _("User created successfully"),
                    "email": user.email
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(
            request.user.profile, context={"request": request})
        return Response(serializer.data)

    def put(self, request):
        serializer = ProfileUpdateSerializer(
            request.user.profile,
            data=request.data,
            partial=True,
            context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            detail_serializer = ProfileSerializer(
                request.user.profile,
                context={"request": request}
            )
            return Response(detail_serializer.data)

        return Response(serializer.errors, status=400)


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response({"error": _("Refresh token is required")}, status=400)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": _("Logged out successfully")})
        except TokenError:
            return Response({"error": _("Invalid or expired token")}, status=400)


class ChangePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data["new_password"])
            user.save()

            return Response({"message": _("Password updated successfully")})

        return Response(serializer.errors, status=400)


class ForgotPasswordAPIView(APIView):
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": _("If an account with this email exists, a reset link has been sent.")},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordConfirmAPIView(APIView):
    def post(self, request):
        serializer = ResetPasswordConfirmSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": _("Password has been reset successfully.")},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    