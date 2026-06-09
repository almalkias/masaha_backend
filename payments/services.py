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

    def _calculate_totals(self, coupon=None):
        items = self._get_cart_items()

        if not items.exists():
            raise PaymentValidationError("Cart is empty.")

        tax_rate = Decimal(str(settings.TAX_RATE))
        subtotal = Decimal("0.00")

        for item in items:
            subtotal += item.product.price

        if subtotal <= 0:
            raise PaymentValidationError("Invalid cart total.")

        discount_amount = coupon.calculate_discount(subtotal) if coupon else Decimal("0.00")
        discounted = subtotal - discount_amount
        tax_amount = (discounted * tax_rate).quantize(Decimal("0.01"))
        total = discounted + tax_amount

        return subtotal, discount_amount, tax_amount, total

    def _generate_idempotency_key(self, total, coupon_code=""):
        cart_data = [
            {
                "id": item.id,
            }
            for item in self._get_cart_items()
        ]

        raw_string = json.dumps({
            "user": self.user.id,
            "cart": cart_data,
            "total": str(total),
            "coupon": coupon_code,
        }, sort_keys=True)

        return hashlib.md5(raw_string.encode()).hexdigest()

    def _create_order(self, coupon, subtotal, discount_amount, tax_amount, total):
        from order.models import Order, OrderItem

        items = self._get_cart_items()

        order = Order.objects.create(user=self.user)

        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=1,
                price=item.product.price,
            )

        order.coupon_code = coupon.code if coupon else ""
        order.discount_amount = discount_amount
        order.tax_amount = tax_amount
        order.total_price = total
        order.save()

        return order

    def _cancel_stale_pending_payments(self):
        from order.models import Order

        stale_payments = Payment.objects.filter(
            user=self.user,
            status=Payment.STATUS_PENDING,
        ).select_related("order")

        for payment in stale_payments:
            try:
                stripe.PaymentIntent.cancel(payment.stripe_payment_intent_id)
            except stripe.error.StripeError:
                pass
            payment.status = Payment.STATUS_FAILED
            payment.save()
            if payment.order:
                payment.order.status = Order.STATUS_CANCELLED
                payment.order.save()

    def create_payment_intent(self, coupon_code=""):
        from coupons.models import Coupon

        coupon = None
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code)
                coupon.validate_for_user(self.user)
            except Coupon.DoesNotExist:
                raise PaymentValidationError("Coupon not found.")

        subtotal, discount_amount, tax_amount, total = self._calculate_totals(coupon=coupon)
        idempotency_key = self._generate_idempotency_key(total, coupon_code)

        self._cancel_stale_pending_payments()

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

        # If a payment already exists for this intent, reuse it — no new order
        existing_payment = Payment.objects.filter(
            stripe_payment_intent_id=intent.id
        ).first()

        if existing_payment:
            return {
                "payment": existing_payment,
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id,
                "subtotal": str(subtotal),
                "discount_amount": str(discount_amount),
                "tax_amount": str(tax_amount),
                "amount": str(total),
                "currency": self.CURRENCY,
            }

        order = self._create_order(coupon, subtotal, discount_amount, tax_amount, total)

        payment = Payment.objects.create(
            stripe_payment_intent_id=intent.id,
            user=self.user,
            order=order,
            amount=total,
            currency=self.CURRENCY,
            status=Payment.STATUS_PENDING,
        )

        return {
            "payment": payment,
            "client_secret": intent.client_secret,
            "payment_intent_id": intent.id,
            "subtotal": str(subtotal),
            "discount_amount": str(discount_amount),
            "tax_amount": str(tax_amount),
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
