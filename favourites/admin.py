from django.contrib import admin
from .models import Favourite


@admin.register(Favourite)
class FavouriteAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "created_at")
    list_display_links = ("user", "product")
    list_filter = ("created_at", "product")
    search_fields = ("user__email", "product__name")
    ordering = ("-created_at",)
    