from django.db import models
from accounts.models import CustomUser
from products.models import Product


class Favourite(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="favourites"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="favourited_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "product"]

    def __str__(self):
        return f"{self.user} - {self.product}"
    