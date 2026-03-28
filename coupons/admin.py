from django.contrib import admin
from .models import Coupon, CouponUsage


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_type", "discount_value", "times_used", "max_uses", "is_active", "expires_at")
    search_fields = ("code",)
    list_filter = ("discount_type", "is_active")


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ("coupon", "user", "used_at")
    search_fields = ("coupon__code", "user__email")
