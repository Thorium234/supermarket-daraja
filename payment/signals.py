# # payment/signals.py
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django.utils.translation import gettext_lazy as _
# from .models import Payment, StockDeductionLog
# from .utils import apply_stock_deduction


# @receiver(post_save, sender=Payment)
# def handle_payment_success(sender, instance, created, **kwargs):
#     """
#     When a Payment is marked SUCCESS:
#     - Mark order as PAID (if not already).
#     - Deduct stock (only once, via utils).
#     - Logdeduction is handled by utils.
#     """
#     if instance.status != "SUCCESS":
#         return

#     order = instance.order

#     # Ensure order is marked PAID (payment success means money is in)
#     # if order.status not in ["PAID", "STOCK_DEDUCTED", "REFUNDED"]:
#         order.status = "PAID"
#         order.save(update_fields=["status"])

#     # Deduct stock idempotently
#     applied = apply_stock_deduction(order, payment=instance, source=StockDeductionLog.AUTO)

#     if applied:
#         # utils already sets status = "STOCK_DEDUCTED", so no double save needed
#         pass



from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Payment, StockDeductionLog
from .utils import apply_stock_deduction


@receiver(post_save, sender=Payment)
def handle_payment_success(sender, instance, created, **kwargs):
    """
    Triggered whenever a Payment is saved.
    If status == SUCCESS:
      - Mark the order as PAID (if not already).
      - Deduct stock once, via apply_stock_deduction().
    """
    if instance.status != Payment.STATUS_SUCCESS:
        return

    order = instance.order

    # ✅ Ensure order is marked PAID
    if order.status not in [order.STATUS_PAID, order.STATUS_STOCK_DEDUCTED, order.STATUS_REFUNDED]:
        order.status = order.STATUS_PAID
        order.save(update_fields=["status"])

    # ✅ Deduct stock safely (idempotent)
    applied = apply_stock_deduction(order, payment=instance, source=StockDeductionLog.AUTO)

    if applied:
        # apply_stock_deduction handles status update to STOCK_DEDUCTED
        return
