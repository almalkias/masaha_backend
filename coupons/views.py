from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from payments.exceptions import PaymentValidationError
from cart.models import Cart
from .models import Coupon
from .serializers import CouponValidateSerializer, CouponSerializer


class ValidateCouponAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CouponValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data["code"]

        try:
            coupon = Coupon.objects.get(code=code)
            coupon.validate_for_user(request.user)
        except Coupon.DoesNotExist:
            return Response({"error": "Coupon not found."}, status=status.HTTP_404_NOT_FOUND)
        except PaymentValidationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        cart = Cart.objects.prefetch_related("items__product").get(user=request.user)
        subtotal = sum(item.product.price for item in cart.items.all())
        discount_amount = coupon.calculate_discount(subtotal)

        data = CouponSerializer(coupon).data
        data["discount_amount"] = str(discount_amount)
        return Response(data)
