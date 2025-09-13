# product/models.py
from django.db import models
from django.utils import timezone
import uuid
from django.contrib.auth.models import User


class Shelf(models.Model):
    """Represents a physical shelf in the supermarket."""
    name = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=150, blank=True, null=True)  # e.g., "Aisle 2 - Left"
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.location if self.location else 'No location'})"


class Product(models.Model):
    """Represents an item in the supermarket."""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    barcode = models.CharField(max_length=100, unique=True, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    shelf = models.ForeignKey(Shelf, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.stock} in stock)"


class Customer(models.Model):
    """Represents a supermarket customer."""
    name = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.phone_number


from django.db import models

class Order(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PAID", "Paid"),
        ("FAILED", "Failed"),
        ("CANCELLED", "Cancelled"),
        ("REFUNDED", "Refunded"),
    ]

    customer = models.ForeignKey("product.Customer", null=True, blank=True, on_delete=models.SET_NULL)
    customer_name = models.CharField(max_length=255, default="Guest")
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)
    stock_deducted = models.BooleanField(default=False)
    def __str__(self):
        return f"Order {self.id} - {self.customer_name} ({self.status})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("product.Product", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=12, decimal_places=2)

    def subtotal(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Order {self.order.id})"


class VerificationLog(models.Model):
    """Logs receipt/order verification attempts (via QR)."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="verifications")
    verified_at = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    verified_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"Verification for Order {self.order.id} at {self.verified_at}"
