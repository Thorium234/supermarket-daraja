from django.test import TestCase, override_settings

from product.models import Category, Product
from product.services.product_service import ProductCatalogService


@override_settings(UNSPLASH_ACCESS_KEY="")
class ProductCatalogServiceTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Groceries", slug="groceries")
        Product.objects.create(name="Milk", category=self.category, price=120, stock=15)
        Product.objects.create(name="Sugar", category=self.category, price=200, stock=5)

    def test_list_products_with_pagination_and_sort(self):
        result = ProductCatalogService.list_products(sort="price_desc", page=1, page_size=10)
        self.assertIn("items", result)
        self.assertEqual(result["pagination"]["total"], 2)
        self.assertEqual(result["items"][0]["name"], "Sugar")

    def test_list_products_category_filter(self):
        result = ProductCatalogService.list_products(category="groceries")
        self.assertEqual(result["pagination"]["total"], 2)
