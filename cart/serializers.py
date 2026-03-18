from django.shortcuts import get_object_or_404
from rest_framework import serializers
from .models import CartItem
from products.models import Product


class AddToCartSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True)
    )
    quantity = serializers.IntegerField(min_value=1)

    def validate(self, data):
        product = data["product"]
        quantity = data["quantity"]

        if quantity > product.stock:
            raise serializers.ValidationError(
                {"quantity": f"Only {product.stock} items available"}
            )

        return data


class ProductInCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "price", "image"]


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductInCartSerializer()

    class Meta:
        model = CartItem
        fields = ["product", "quantity"]


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)

    def validate_quantity(self, value):
        cart_item = self.context.get("cart_item")

        if not cart_item:
            return value  # fallback (احتياطي)

        if value > cart_item.product.stock:
            raise serializers.ValidationError(
                f"Only {cart_item.product.stock} items available"
            )

        return value
