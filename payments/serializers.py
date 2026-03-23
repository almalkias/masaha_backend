from rest_framework import serializers


class CreatePaymentIntentSerializer(serializers.Serializer):
    pass


class VerifyPaymentSerializer(serializers.Serializer):
    payment_intent_id = serializers.CharField()
