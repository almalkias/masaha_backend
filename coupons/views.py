from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from payments.exceptions import PaymentValidationError
from .models import Coupon
from .serializers import CouponValidateSerializer, CouponSerializer


class ValidateCouponAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = CouponValidateSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data["code"]

        try:
            coupon = Coupon.objects.get(code=code)
            coupon.validate_for_user(request.user)
        except Coupon.DoesNotExist:
            return Response({"error": "Coupon not found."}, status=status.HTTP_404_NOT_FOUND)
        except PaymentValidationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(CouponSerializer(coupon).data)
