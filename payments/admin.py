from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):

    # Columns shown in the list view
    list_display = (
        "id",
        "user",
        "amount",
        "currency",
        "status",
        "stripe_payment_intent_id",
        "created_at",
    )

    # List filters
    list_filter = (
        "status",
        "currency",
        "created_at",
    )

    # Search fields
    search_fields = (
        "user__email",
        "stripe_payment_intent_id",
    )

    # Default ordering
    ordering = ("-created_at",)

    # Read-only fields
    readonly_fields = (
        "order",
        "stripe_payment_intent_id",
        "amount",
        "currency",
        "status",
        "created_at",
    )

    # Improve the admin page layout
    fieldsets = (
        ("Payment Info", {
            "fields": (
                "user",
                "order",
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
