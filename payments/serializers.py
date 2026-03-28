from rest_framework import serializers


class CreatePaymentIntentSerializer(serializers.Serializer):
    coupon_code = serializers.CharField(required=False, allow_blank=True, default="")
