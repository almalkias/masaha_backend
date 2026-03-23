from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import CustomUser
from products.models import Product

from .models import CartItem


class ClearCartAPIViewTests(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="cart@example.com",
            password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

        self.product_1 = Product.objects.create(
            name="Product 1",
            description="First product",
            price="10.00",
            stock=10
        )
        self.product_2 = Product.objects.create(
            name="Product 2",
            description="Second product",
            price="15.00",
            stock=10
        )

        self.cart = self.user.cart
        CartItem.objects.create(cart=self.cart, product=self.product_1, quantity=2)
        CartItem.objects.create(cart=self.cart, product=self.product_2, quantity=1)

    def test_delete_clear_removes_all_cart_items(self):
        response = self.client.delete("/api/cart/clear/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Cart cleared")
        self.assertEqual(response.data["deleted_items"], 2)
        self.assertTrue(self.user.cart.pk)
        self.assertEqual(self.cart.items.count(), 0)
