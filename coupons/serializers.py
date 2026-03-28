from rest_framework import serializers
from .models import Coupon


class CouponValidateSerializer(serializers.Serializer):
    code = serializers.CharField()


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ["code", "discount_type", "discount_value"]
