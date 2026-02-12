from django.db import transaction

from .models import Payment, StockDeductionLog


FINAL_ORDER_STATES = {"PAID", "SHIPPED", "DELIVERED", "REFUNDED", "CANCELLED", "FAILED"}


def apply_stock_deduction(order, payment=None, user=None, source=StockDeductionLog.AUTO):
    """Deduct stock once for an order and log per item entries."""
    if StockDeductionLog.objects.filter(
        order=order,
        payment=payment,
        action=StockDeductionLog.DEDUCT,
    ).exists():
        return False

    with transaction.atomic():
        for item in order.items.select_related("product"):
            product = item.product
            if product.stock < item.quantity:
                raise ValueError(f"Insufficient stock for {product.name}")
            product.stock -= item.quantity
            product.save(update_fields=["stock"])

            StockDeductionLog.objects.create(
                order=order,
                payment=payment,
                product=product,
                quantity=item.quantity,
                action=StockDeductionLog.DEDUCT,
                source=source,
                deducted_by=user,
            )

    return True


def rollback_stock_deduction(order, payment=None, user=None):
    """Restore stock once for an order and log rollback entries."""
    if StockDeductionLog.objects.filter(
        order=order,
        payment=payment,
        action=StockDeductionLog.ROLLBACK,
    ).exists():
        return False

    with transaction.atomic():
        for item in order.items.select_related("product"):
            product = item.product
            product.stock += item.quantity
            product.save(update_fields=["stock"])

            StockDeductionLog.objects.create(
                order=order,
                payment=payment,
                product=product,
                quantity=item.quantity,
                action=StockDeductionLog.ROLLBACK,
                source=StockDeductionLog.MANUAL,
                deducted_by=user,
            )

    return True


def refund_order(payment, user=None):
    """Issue refund and rollback stock."""
    order = payment.order
    if payment.status != Payment.STATUS_PAID:
        return False, "Only paid payments can be refunded."

    rollback_ok = rollback_stock_deduction(order, payment=payment, user=user)
    if not rollback_ok:
        return False, "Rollback already applied."

    with transaction.atomic():
        payment.status = Payment.STATUS_REFUNDED
        payment.save(update_fields=["status"])
        order.status = "REFUNDED"
        order.save(update_fields=["status"])

    return True, "Refund processed successfully."
