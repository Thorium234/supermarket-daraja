from django.test import TestCase
from django.urls import reverse

from product.models import Product


class FrontendSmokeTests(TestCase):
    def setUp(self):
        Product.objects.create(name="Milk", price=120, stock=10)

    def test_homepage_renders_catalog(self):
        response = self.client.get(reverse("product:product_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Shop")
        self.assertContains(response, "Milk")

    def test_cart_page_renders(self):
        response = self.client.get(reverse("product:cart"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cart")
