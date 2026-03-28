from rest_framework import serializers
from order.models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name")

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_name", "quantity", "price"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ["id", "subtotal", "tax_amount", "total_price", "created_at", "items", "status"]

    def get_subtotal(self, obj):
        return str(obj.total_price - obj.tax_amount)
