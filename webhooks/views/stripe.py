import stripe
from django.conf import settings
from django.db import transaction

from rest_framework.views import APIView
from rest_framework.response import Response

from payments.models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeWebhookAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                settings.STRIPE_WEBHOOK_SECRET
            )
        except Exception:
            return Response({"error": "Invalid webhook"}, status=400)

        if event["type"] == "payment_intent.succeeded":
            self.handle_payment_success(event["data"]["object"])

        return Response({"status": "ok"})

    def handle_payment_success(self, intent):
        payment_intent_id = intent["id"]
        print("🔥 Processing payment:", payment_intent_id)

        payment = Payment.objects.select_related("order", "user").filter(
            stripe_payment_intent_id=payment_intent_id
        ).first()

        if not payment:
            print(f"❌ Payment not found for intent: {payment_intent_id}")
            return

        # Prevent duplicate processing at the payment level
        if payment.status == Payment.STATUS_SUCCEEDED:
            print("⚠️ Payment already processed")
            return

        try:
            with transaction.atomic():
                # Update the payment status
                payment.status = Payment.STATUS_SUCCEEDED
                payment.save()

                print("✅ Payment marked as succeeded")

                # Finalize the order
                self.finalize_order(payment)

        except Exception as e:
            print(f"❌ Error processing webhook: {str(e)}")
            # Return 200 so Stripe does not keep retrying the webhook
            return

    def finalize_order(self, payment):
        from cart.models import Cart

        order = payment.order
        user = payment.user

        if not order:
            print("❌ No order linked to payment")
            return

        # Prevent duplicate processing at the order level
        if getattr(order, "status", None) == "paid":
            print("⚠️ Order already finalized")
            return

        print(f"🚀 Finalizing order {order.id}")

        subtotal = 0

        for item in order.items.select_related("product").all():
            product = item.product

            if item.quantity > product.stock:
                raise Exception(
                    f"Not enough stock for {product.name}"
                )

            product.stock -= item.quantity
            product.save()

            subtotal += item.price * item.quantity

        order.total_price = subtotal + order.tax_amount
        if hasattr(order, "status"):
            order.status = "paid"
        order.save()

        if order.coupon_code:
            from django.db.models import F
            from coupons.models import Coupon, CouponUsage
            coupon = Coupon.objects.filter(code=order.coupon_code).first()
            if coupon:
                CouponUsage.objects.get_or_create(coupon=coupon, user=user)
                Coupon.objects.filter(pk=coupon.pk).update(times_used=F("times_used") + 1)

        # Clear the cart after a successful payment
        Cart.objects.filter(user=user).delete()

        print("✅ Order finalized + cart cleared")
