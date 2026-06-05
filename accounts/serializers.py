from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import CustomUser, Profile

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
import resend
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        # Add user data
        data["user"] = {
            "id": self.user.id,
            "email": self.user.email,
        }

        return data


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ["email", "password", "password_confirm"]

    def validate(self, data):
        password = data.get("password")
        password_confirm = data.get("password_confirm")

        if password != password_confirm:
            raise serializers.ValidationError({
                "password_confirm": "Passwords do not match."
            })

        validate_password(password)

        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        # create_user hashes the password before saving
        return CustomUser.objects.create_user(**validated_data)


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField()
    confirm_password = serializers.CharField()

    def validate(self, data):
        user = self.context["request"].user

        # Validate the current password
        if not user.check_password(data["current_password"]):
            raise serializers.ValidationError({
                "current_password": "Current password is incorrect."
            })

        # Validate password confirmation
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match."
            })

        # Validate password strength using Django validators
        validate_password(data["new_password"])

        return data


class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            "first_name",
            "last_name",
            "country",
            "city",
            "birth_date",
            "email",
            "image_url",
        ]

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class ProfileUpdateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", required=False)

    class Meta:
        model = Profile
        fields = [
            "first_name",
            "last_name",
            "country",
            "city",
            "birth_date",
            "email",
            "image",
        ]

    def validate(self, attrs):
        user_data = attrs.get("user")

        if user_data and "email" in user_data:
            new_email = user_data["email"]
            current_email = self.instance.user.email if self.instance and self.instance.user else None

            if current_email and new_email.strip().lower() == current_email.strip().lower():
                raise serializers.ValidationError({
                    "email": "The new email address is the same as the current one."
                })

            if CustomUser.objects.filter(email__iexact=new_email).exists():
                raise serializers.ValidationError({
                    "email": "This email is already in use."
                })

        return attrs

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", None)

        if user_data:
            instance.user.email = user_data.get("email", instance.user.email)
            instance.user.save()

        if "image" in validated_data and instance.image:
            instance.image.delete(save=False)

        return super().update(instance, validated_data)


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def save(self):
        email = self.validated_data["email"]

        user = CustomUser.objects.filter(email__iexact=email).first()

        if not user:
            return

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        frontend_url = getattr(settings, "FRONTEND_URL")
        reset_link = f"{frontend_url}/reset-password-confirm?uid={uid}&token={token}"

        resend.api_key = settings.RESEND_API_KEY
        resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": user.email,
            "subject": "Reset your password",
            "html": f"<p>Use this link to reset your password:</p><p><a href='{reset_link}'>{reset_link}</a></p>",
        })


class ResetPasswordConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        uid = data.get("uid")
        token = data.get("token")
        new_password = data.get("new_password")
        confirm_password = data.get("confirm_password")

        if new_password != confirm_password:
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match."
            })

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = CustomUser.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            raise serializers.ValidationError({
                "uid": "Invalid reset link."
            })

        if not default_token_generator.check_token(user, token):
            raise serializers.ValidationError({
                "token": "Invalid or expired reset token."
            })

        validate_password(new_password, user)

        data["user"] = user
        return data

    def save(self):
        user = self.validated_data["user"]
        new_password = self.validated_data["new_password"]

        user.set_password(new_password)
        user.save()

        return user
    