from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Payment


@receiver(post_save, sender=Payment)
def sync_order_status_with_payment(sender, instance, **kwargs):
    """Keep order status aligned with final payment state."""
    order = instance.order
    if instance.status == Payment.STATUS_PAID and order.status not in ("PAID", "SHIPPED", "DELIVERED"):
        order.status = "PAID"
        order.save(update_fields=["status"])
    elif instance.status == Payment.STATUS_FAILED and order.status == "PENDING":
        order.status = "FAILED"
        order.save(update_fields=["status"])
    elif instance.status == Payment.STATUS_REFUNDED and order.status != "REFUNDED":
        order.status = "REFUNDED"
        order.save(update_fields=["status"])
