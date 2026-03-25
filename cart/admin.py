from django.contrib import admin
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at", "items_display")
    inlines = [CartItemInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("items__product")

    def items_display(self, obj):
        items = obj.items.all()

        if not items:
            return "-"

        return ", ".join(
            f"{item.product.name} x{item.quantity}"
            for item in items
        )

    items_display.short_description = "Cart Items"


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("id", "cart", "product", "quantity")
