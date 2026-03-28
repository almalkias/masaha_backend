from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .serializers import CreatePaymentIntentSerializer
from .services import PaymentService
from .exceptions import PaymentError, PaymentValidationError, PaymentGatewayError


class CreatePaymentIntentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreatePaymentIntentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = PaymentService(user=request.user)

        try:
            result = service.create_payment_intent()
        except PaymentValidationError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except PaymentGatewayError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY
            )

        return Response(
            {
                "client_secret": result["client_secret"],
                "payment_intent_id": result["payment_intent_id"],
                "subtotal": result["subtotal"],
                "tax_amount": result["tax_amount"],
                "amount": result["amount"],
                "currency": result["currency"],
            },
            status=status.HTTP_201_CREATED
        )
