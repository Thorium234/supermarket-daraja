from django.contrib import admin, messages
from django.urls import path, reverse
from django.shortcuts import redirect, render
from django.utils.html import format_html, mark_safe
from django.db import transaction

from .models import Payment, StockDeductionLog
from product.models import Product, Order


# -------------------- Stock Deduction Log Admin -------------------- #
@admin.register(StockDeductionLog)
class StockDeductionLogAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "payment", "product", "quantity", "action", "source", "deducted_by", "created_at")
    list_filter = ("action", "source", "created_at")
    search_fields = ("order__id", "payment__id", "product__name", "deducted_by__username")
    readonly_fields = ("created_at",)

    def save_model(self, request, obj, form, change):
        """Auto-fill deducted_by + adjust stock if manual DEDUCT."""
        if not obj.deducted_by:
            obj.deducted_by = request.user
        super().save_model(request, obj, form, change)

        if obj.action == StockDeductionLog.DEDUCT and obj.source == StockDeductionLog.MANUAL:
            try:
                with transaction.atomic():
                    product = obj.product
                    if product.stock < obj.quantity:
                        raise ValueError(
                            f"Not enough stock for {product.name}. "
                            f"Available: {product.stock}, Tried to deduct: {obj.quantity}"
                        )
                    product.stock -= obj.quantity
                    product.save()
                    messages.success(
                        request,
                        f"✅ Stock reduced: {obj.quantity}x {product.name} (manual deduct by {request.user.username})",
                    )
            except Exception as e:
                messages.error(request, f"❌ Failed to adjust stock: {e}")


# -------------------- Payment Admin -------------------- #
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "status",
        "amount",
        "mpesa_receipt_no",
        "transaction_date",
        "rolled_back_status",
        "rollback_button",
    )
    list_filter = ("status",)
    readonly_fields = ("rolled_back_status",)
    actions = ["manual_stock_rollback"]

    def rolled_back_status(self, obj):
        if StockDeductionLog.objects.filter(payment=obj, source=StockDeductionLog.ROLLBACK).exists():
            return mark_safe('<span style="color: red; font-weight: bold;">✔ Rolled Back</span>')
        return mark_safe('<span style="color: green; font-weight: bold;">—</span>')
    rolled_back_status.short_description = "Rolled Back?"

    def rollback_button(self, obj):
        if StockDeductionLog.objects.filter(payment=obj, source=StockDeductionLog.ROLLBACK).exists():
            return mark_safe('<span style="color: gray;">Rollback disabled</span>')
        url = reverse("admin:payment-rollback", args=[obj.pk])
        return format_html(
            '<a class="button" href="{}" '
            'style="padding:4px 8px; background:#d9534f; color:white; border-radius:4px;">Rollback</a>',
            url,
        )
    rollback_button.short_description = "Actions"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "rollback/<int:payment_id>/",
                self.admin_site.admin_view(self.rollback_view),
                name="payment-rollback",
            ),
        ]
        return custom_urls + urls

    def rollback_view(self, request, payment_id):
        payment = Payment.objects.get(pk=payment_id)

        if request.method == "POST":
            if payment.status == Payment.STATUS_PAID and not self._already_rolled_back(payment):
                rollback_stock_deduction(payment, request.user)
                self.message_user(
                    request,
                    f"✅ Rolled back stock for Payment {payment.id}",
                    level=messages.SUCCESS,
                )
            else:
                self.message_user(
                    request,
                    f"⚠ Payment {payment.id} cannot be rolled back (invalid status or already rolled back).",
                    level=messages.WARNING,
                )
            return redirect(f"../../{payment_id}/change/")

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "payment": payment,
            "already_rolled_back": self._already_rolled_back(payment),
        }
        return render(request, "admin/payment_rollback_confirm.html", context)

    def manual_stock_rollback(self, request, queryset):
        count = 0
        for payment in queryset:
            if payment.status == Payment.STATUS_PAID and not self._already_rolled_back(payment):
                rollback_stock_deduction(payment, request.user)
                count += 1
            else:
                self.message_user(
                    request,
                    f"⚠ Payment {payment.id} skipped (status={payment.status} or already rolled back).",
                    level=messages.WARNING,
                )

        if count:
            self.message_user(
                request,
                f"✅ Rolled back stock for {count} payment(s).",
                level=messages.SUCCESS,
            )

    manual_stock_rollback.short_description = "🔄 Manual rollback stock for selected payments"

    def _already_rolled_back(self, payment):
        return StockDeductionLog.objects.filter(
            payment=payment, source=StockDeductionLog.ROLLBACK
        ).exists()


# -------------------- Shared rollback helper -------------------- #
def rollback_stock_deduction(payment, user):
    """Utility to rollback stock for a payment."""
    order = payment.order
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
            )
