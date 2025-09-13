# payment/utils.py
from django.db import transaction
from .models import StockDeductionLog


def apply_stock_deduction(order, payment=None, user=None, source=StockDeductionLog.AUTO):
    """
    Deduct stock for all items in the order and log it.
    Idempotent: will not double-deduct if already logged.
    Returns True if deduction applied, False otherwise.
    """
    if StockDeductionLog.objects.filter(order=order, payment=payment, source=source, action=StockDeductionLog.DEDUCT).exists():
        return False  # already deducted

    with transaction.atomic():
        for item in order.items.all():
            product = item.product
            product.stock = max(product.stock - item.quantity, 0)
            product.save()

            StockDeductionLog.objects.create(
                order=order,
                payment=payment,
                product=product,
                quantity=item.quantity,
                action=StockDeductionLog.DEDUCT,
                source=source,
                deducted_by=user,
                notes=f"Deducted {item.quantity} × {product.name} for order {order.id}",
            )

        order.status = "STOCK_DEDUCTED"
        order.save(update_fields=["status"])

    return True


def rollback_stock_deduction(order, payment=None, user=None, notes=""):
    """
    Restore stock for an order and log the rollback.
    Idempotent: will not rollback twice.
    Returns True if rollback applied, False otherwise.
    """
    if StockDeductionLog.objects.filter(order=order, payment=payment, source=StockDeductionLog.ROLLBACK, action=StockDeductionLog.ROLLBACK).exists():
        return False  # already rolled back

    with transaction.atomic():
        for item in order.items.all():
            product = item.product
            product.stock += item.quantity
            product.save()

            StockDeductionLog.objects.create(
                order=order,
                payment=payment,
                product=product,
                quantity=item.quantity,
                action=StockDeductionLog.ROLLBACK,
                source=StockDeductionLog.MANUAL,
                deducted_by=user,
                notes=f"Rollback {item.quantity} × {product.name} for order {order.id}. {notes}",
            )

        # keep PAID if no refund flow, otherwise admin will set REFUNDED
        order.status = "PAID"
        order.save(update_fields=["status"])

    return True


def refund_order(payment, user=None, notes="Refund issued"):
    """
    Mark a payment as REFUNDED and rollback stock.
    Returns (success, message).
    """
    order = payment.order

    if payment.status != "SUCCESS":
        return False, "Only successful payments can be refunded."

    rollback_ok = rollback_stock_deduction(order, payment=payment, user=user, notes=notes)
    if not rollback_ok:
        return False, "Rollback already applied or not needed."

    with transaction.atomic():
        payment.status = "REFUNDED"
        payment.save(update_fields=["status"])

        order.status = "REFUNDED"
        order.save(update_fields=["status"])

        StockDeductionLog.objects.create(
            order=order,
            payment=payment,
            product=None,   # not tied to a single product
            quantity=0,     # aggregate
            action=StockDeductionLog.ROLLBACK,
            source=StockDeductionLog.MANUAL,
            deducted_by=user,
            notes=f"Refund issued: {notes}",
        )

    return True, "Refund processed successfully."
