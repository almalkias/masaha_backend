from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.timezone import now


class Coupon(models.Model):
    PERCENTAGE = "percentage"
    FIXED = "fixed"
    DISCOUNT_TYPE_CHOICES = [
        (PERCENTAGE, "Percentage"),
        (FIXED, "Fixed"),
    ]

    code = models.CharField(max_length=50, unique=True, db_index=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    max_uses = models.PositiveIntegerField(null=True, blank=True)
    times_used = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.code

    def calculate_discount(self, subtotal):
        if self.discount_type == self.PERCENTAGE:
            return (subtotal * self.discount_value / 100).quantize(Decimal("0.01"))
        return min(self.discount_value, subtotal)

    def validate_for_user(self, user):
        from payments.exceptions import PaymentValidationError

        if not self.is_active:
            raise PaymentValidationError("This coupon is no longer active.")
        if self.expires_at and now() > self.expires_at:
            raise PaymentValidationError("This coupon has expired.")
        if self.max_uses is not None and self.times_used >= self.max_uses:
            raise PaymentValidationError("This coupon has reached its usage limit.")
        if CouponUsage.objects.filter(coupon=self, user=user).exists():
            raise PaymentValidationError("You have already used this coupon.")


class CouponUsage(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name="usages")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("coupon", "user")

    def __str__(self):
        return f"{self.user.email} used {self.coupon.code}"
