from rest_framework import serializers
from .models import CartItem
from products.models import Product
from products.serializers import ProductSerializer


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


class CartItemSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["id", "product", "quantity"]

    def get_product(self, obj):
        return ProductSerializer(
            obj.product,
            context=self.context
        ).data


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)

    def validate_quantity(self, value):
        cart_item = self.context.get("cart_item")

        if not cart_item:
            return value  # Fallback if the cart item context is missing

        if value > cart_item.product.stock:
            raise serializers.ValidationError(
                f"Only {cart_item.product.stock} items available"
            )

        return value
