# product/models.py
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class Shelf(models.Model):
    """Represents a physical shelf in the supermarket."""
    name = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=150, blank=True, null=True)  # e.g., "Aisle 2 - Left"
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.location if self.location else 'No location'})"


class Category(models.Model):
    """Logical product categorization for storefront and filtering."""
    name = models.CharField(max_length=120, unique=True, db_index=True)
    slug = models.SlugField(max_length=140, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("name",)
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name


class Product(models.Model):
    """Represents an item in the supermarket."""
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    category = models.ForeignKey("product.Category", on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    barcode = models.CharField(max_length=100, unique=True, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, db_index=True)
    discount_percentage = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(90)],
        help_text="Discount percentage from 0 to 90.",
    )
    stock = models.PositiveIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    shelf = models.ForeignKey(Shelf, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["price"]),
            models.Index(fields=["stock"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.stock} in stock)"

    @property
    def discounted_price(self):
        if not self.discount_percentage:
            return self.price
        multiplier = Decimal(100 - self.discount_percentage) / Decimal(100)
        return self.price * multiplier


class Customer(models.Model):
    """Represents a supermarket customer."""
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="customer_profile")
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
        ("SHIPPED", "Shipped"),
        ("DELIVERED", "Delivered"),
        ("FAILED", "Failed"),
        ("CANCELLED", "Cancelled"),
        ("REFUNDED", "Refunded"),
    ]

    customer = models.ForeignKey("product.Customer", null=True, blank=True, on_delete=models.SET_NULL)
    customer_name = models.CharField(max_length=255, default="Guest")
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    stock_deducted = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["created_at"]),
        ]

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


class ProductReview(models.Model):
    """Customer product reviews and ratings."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(fields=["product", "customer"], name="unique_product_review_per_customer"),
        ]
        indexes = [
            models.Index(fields=["product", "created_at"]),
            models.Index(fields=["rating"]),
        ]

    def __str__(self):
        return f"{self.product.name} review ({self.rating}/5)"


class Cart(models.Model):
    """Persistent customer cart for authenticated flows and recovery."""
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name="cart")
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    def __str__(self):
        return f"Cart({self.customer_id})"


class CartItem(models.Model):
    """Item in a persistent cart."""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="cart_items")
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["cart", "product"], name="unique_cart_product"),
        ]
        indexes = [
            models.Index(fields=["cart", "created_at"]),
            models.Index(fields=["product"]),
        ]

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
