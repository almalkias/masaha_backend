from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.exceptions import ValidationError

from django.db import transaction

from cart.models import Cart
from order.serializers import OrderSerializer
from .models import Order, OrderItem


class CheckoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)

        cart_items = cart.items.select_related("product").all()

        # ❌ السلة فاضية
        if not cart_items.exists():
            return Response(
                {"error": "Cart is empty"},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            order = Order.objects.create(user=request.user)
            total_price = 0

            for item in cart_items:
                product = item.product

                # 🔴 تحقق من المخزون
                if item.quantity > product.stock:
                    raise ValidationError(
                        f"Not enough stock for {product.name}"
                    )

                # ✅ إنشاء OrderItem
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item.quantity,
                    price=product.price
                )

                # 🔥 خصم المخزون
                product.stock -= item.quantity
                product.save()

                # ✅ حساب الإجمالي
                total_price += product.price * item.quantity

            # ✅ تحديث الطلب
            order.total_price = total_price
            order.save()

            # 🧹 تفريغ السلة
            cart_items.delete()

        return Response(
            {
                "message": "Order created successfully",
                "order_id": order.id,
                "total_price": total_price
            },
            status=status.HTTP_201_CREATED
        )


class OrderListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user)

        serializer = OrderSerializer(orders, many=True)

        return Response(serializer.data)
    