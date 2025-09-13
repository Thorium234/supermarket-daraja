# payment/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone

class Payment(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_PAID = "PAID"
    STATUS_FAILED = "FAILED"
    STATUS_REFUNDED = "REFUNDED"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PAID, "Paid"),
        (STATUS_FAILED, "Failed"),
        (STATUS_REFUNDED, "Refunded"),
    ]

    # 👇 Linked to product.Order
    order = models.ForeignKey(
        "product.Order", on_delete=models.CASCADE, related_name="payments"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )

    # 👇 Allow null/blank for historical data
    mpesa_receipt_no = models.CharField(max_length=50, null=True, blank=True)
    transaction_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.id} for Order {self.order.id} - {self.status}"



class StockDeductionLog(models.Model):
    # Actions
    DEDUCT = "DEDUCT"
    ROLLBACK = "ROLLBACK"

    # Sources
    AUTO = "AUTO"
    MANUAL = "MANUAL"

    ACTION_CHOICES = [
        (DEDUCT, "Deduct"),
        (ROLLBACK, "Rollback"),
    ]
    SOURCE_CHOICES = [
        (AUTO, "Automatic"),
        (MANUAL, "Manual"),
    ]

    product = models.ForeignKey("product.Product", on_delete=models.CASCADE)
    order = models.ForeignKey("product.Order", on_delete=models.CASCADE)
    payment = models.ForeignKey("payment.Payment", null=True, blank=True, on_delete=models.SET_NULL)
    quantity = models.PositiveIntegerField()
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default=AUTO)
    deducted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="User who manually deducted stock. Null if automatic."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.action} {self.quantity}x {self.product.name} (Order {self.order.id})"
