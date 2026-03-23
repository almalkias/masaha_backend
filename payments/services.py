import hashlib
import json
from decimal import Decimal
import stripe
from django.conf import settings

from cart.models import Cart
from .models import Payment
from .exceptions import PaymentValidationError, PaymentGatewayError

stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentService:
    CURRENCY = "usd"

    def __init__(self, user):
        self.user = user

    def _get_cart(self):
        cart, _ = Cart.objects.get_or_create(user=self.user)
        return cart

    def _get_cart_items(self):
        cart = self._get_cart()
        items = cart.items.select_related("product").all()
        return items

    def _calculate_total(self):
        items = self._get_cart_items()

        if not items.exists():
            raise PaymentValidationError("Cart is empty.")

        total = Decimal("0.00")

        for item in items:
            if item.quantity > item.product.stock:
                raise PaymentValidationError(
                    f"Only {item.product.stock} items available for {item.product.name}."
                )

            total += item.product.price * item.quantity

        if total <= 0:
            raise PaymentValidationError("Invalid cart total.")

        return total

    def _generate_idempotency_key(self, total):
        cart_data = [
            {
                "id": item.id,
                "quantity": item.quantity,
            }
            for item in self._get_cart_items()  # 👈 لازم تكون عندك
        ]

        raw_string = json.dumps({
            "user": self.user.id,
            "cart": cart_data,
            "total": str(total),
        }, sort_keys=True)

        return hashlib.md5(raw_string.encode()).hexdigest()

    def create_payment_intent(self):
        total = self._calculate_total()
        idempotency_key = self._generate_idempotency_key(total)

        try:
            intent = stripe.PaymentIntent.create(
                amount=int(total * 100),
                currency=self.CURRENCY,
                payment_method_types=["card"],
                metadata={
                    "user_id": str(self.user.id),
                },
                idempotency_key=idempotency_key,
            )
        except stripe.error.StripeError as exc:
            raise PaymentGatewayError(str(exc))

        payment, created = Payment.objects.get_or_create(
            stripe_payment_intent_id=intent.id,
            defaults={
                "user": self.user,
                "amount": total,
                "currency": self.CURRENCY,
                "status": Payment.STATUS_PENDING,
            }
        )

        return {
            "payment": payment,
            "client_secret": intent.client_secret,
            "payment_intent_id": intent.id,
            "amount": str(total),
            "currency": self.CURRENCY,
        }

    def verify_payment(self, payment_intent_id):
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        except stripe.error.StripeError as exc:
            raise PaymentGatewayError(str(exc))

        payment = Payment.objects.filter(
            stripe_payment_intent_id=payment_intent_id,
            user=self.user
        ).first()

        if not payment:
            raise PaymentValidationError("Payment not found.")

        if intent.status == "succeeded":
            payment.status = Payment.STATUS_SUCCEEDED
        else:
            payment.status = Payment.STATUS_FAILED

        payment.save()

        return payment
