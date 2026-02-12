import json
from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from product.models import Category, Product, Customer


@override_settings(UNSPLASH_ACCESS_KEY="")
class ProductApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Groceries", slug="groceries")
        Product.objects.create(name="Milk", category=self.category, price=120, stock=15)

    def test_product_list_api(self):
        res = self.client.get(reverse("product_api:product_list_api"))
        self.assertEqual(res.status_code, 200)
        payload = res.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["data"]["pagination"]["total"], 1)


@override_settings(UNSPLASH_ACCESS_KEY="")
class AuthAndOrderApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Groceries", slug="groceries")
        self.product = Product.objects.create(name="Bread", category=self.category, price=80, stock=10)

    def _register(self):
        payload = {
            "username": "apiuser",
            "first_name": "API",
            "last_name": "User",
            "email": "api@example.com",
            "phone_number": "0712345678",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        }
        return self.client.post(
            reverse("product_api:auth_register_api"),
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_register_and_create_order(self):
        reg = self._register()
        self.assertEqual(reg.status_code, 201)
        token = reg.json()["data"]["token"]

        res = self.client.post(
            reverse("product_api:order_create_api"),
            data=json.dumps({"items": [{"product_id": self.product.id, "quantity": 2}]}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(res.status_code, 201)
        self.assertTrue(res.json()["ok"])
