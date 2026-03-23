from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):

    # 🔹 الأعمدة في القائمة
    list_display = (
        "id",
        "user",
        "amount",
        "currency",
        "status",
        "stripe_payment_intent_id",
        "created_at",
    )

    # 🔹 فلترة
    list_filter = (
        "status",
        "currency",
        "created_at",
    )

    # 🔹 البحث
    search_fields = (
        "user__email",
        "stripe_payment_intent_id",
    )

    # 🔹 ترتيب
    ordering = ("-created_at",)

    # 🔹 readonly (مهم جدًا)
    readonly_fields = (
        "stripe_payment_intent_id",
        "amount",
        "currency",
        "status",
        "created_at",
    )

    # 🔹 تحسين العرض داخل الصفحة
    fieldsets = (
        ("Payment Info", {
            "fields": (
                "user",
                "status",
            )
        }),
        ("Stripe Info", {
            "fields": (
                "stripe_payment_intent_id",
                "amount",
                "currency",
            )
        }),
        ("Timestamps", {
            "fields": (
                "created_at",
            )
        }),
    )
