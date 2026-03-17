from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import CustomUser, Profile


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
    class Meta:
        model = Profile
        fields = ["full_name", "phone", "address"]
