from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from django.shortcuts import get_object_or_404

from .models import Cart, CartItem
from .serializers import AddToCartSerializer, CartItemSerializer, UpdateCartItemSerializer


class AddToCartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = serializer.validated_data["product"]
        quantity = serializer.validated_data["quantity"]

        # Get or create the user's cart
        cart, _ = Cart.objects.get_or_create(user=request.user)

        # Check whether the product is already in the cart
        cart_item = CartItem.objects.filter(
            cart=cart,
            product=product
        ).first()

        if cart_item:
            new_quantity = cart_item.quantity + quantity

            # Prevent the quantity from exceeding available stock
            if new_quantity > product.stock:
                return Response(
                    {"error": f"Only {product.stock} items available"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            cart_item.quantity = new_quantity
            cart_item.save()
        else:
            CartItem.objects.create(
                cart=cart,
                product=product,
                quantity=quantity
            )

        return Response(
            {"message": "Product added to cart"},
            status=status.HTTP_200_OK
        )


class CartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)

        items = cart.items.select_related("product").all()
        serializer = CartItemSerializer(items, many=True, context={"request": request})

        return Response({
            "items": serializer.data
        })


class RemoveFromCartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        cart = get_object_or_404(Cart, user=request.user)

        cart_item = get_object_or_404(
            CartItem,
            id=item_id,
            cart=cart
        )

        cart_item.delete()

        return Response({"message": "Item removed from cart"})


class ClearCartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        deleted_count, _ = cart.items.all().delete()

        return Response({
            "message": "Cart cleared",
            "deleted_items": deleted_count
        })


class UpdateCartItemAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, item_id):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item = get_object_or_404(
            CartItem,
            id=item_id,
            cart=cart
        )
        serializer = UpdateCartItemSerializer(
            data=request.data,
            context={"cart_item": cart_item}
        )
        serializer.is_valid(raise_exception=True)
        cart_item.quantity = serializer.validated_data["quantity"]
        cart_item.save()

        return Response({
            "message": "Cart item updated",
            "quantity": cart_item.quantity
        })
