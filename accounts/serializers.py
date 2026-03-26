from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import CustomUser, Profile


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
        email = data.get("email")

        if password != password_confirm:
            raise serializers.ValidationError({
                "password_confirm": "Passwords do not match."
            })

        temp_user = CustomUser(email=email)
        validate_password(password, user=temp_user)

        return data

    def create(self, validated_data):
        # Remove temporary field used only for validation
        validated_data.pop("password_confirm")
        return CustomUser.objects.create_user(**validated_data)


class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", required=False)

    # Write-only upload field
    image = serializers.ImageField(required=False, allow_null=True)

    # Read-only full image URL
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
            "image",      # Used for uploads
            "image_url",  # Used for display
        ]

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

    def update(self, instance, validated_data):
        # Update the email address
        user_data = validated_data.pop("user", None)

        if user_data:
            instance.user.email = user_data.get("email", instance.user.email)
            instance.user.save()

        return super().update(instance, validated_data)


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField()
    confirm_password = serializers.CharField()

    def validate(self, data):
        user = self.context["request"].user

        # Validate the current password
        if not user.check_password(data["current_password"]):
            raise serializers.ValidationError({
                "current_password": "كلمة المرور الحالية غير صحيحة"
            })

        # Validate password confirmation
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError({
                "confirm_password": "كلمة المرور غير متطابقة"
            })

        # Validate password strength using Django validators
        validate_password(data["new_password"], user)

        return data
