# payment/views.py
from decimal import Decimal
import json
import logging
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse

from django_daraja.mpesa.core import MpesaClient

from product.models import Order
from .models import Payment, StockDeductionLog
from .tasks import send_email_task, send_sms_task
from .utils import apply_stock_deduction

logger = logging.getLogger(__name__)
cl = MpesaClient()


# ---------------- Payment Initiation ---------------- #
from django.views.decorators.http import require_POST

@require_POST
def initiate_payment(request, order_id):
    """Trigger M-Pesa STK Push for an order."""
    order = get_object_or_404(Order, id=order_id)
    phone_number = request.POST.get("phone_number")
    if not phone_number:
        return HttpResponse("Phone number is required.", status=400)

    try:
        # ✅ Ensure integer amount for M-Pesa
        amount = int(order.total_price)
    except Exception as exc:
        logger.exception("Invalid order total for order %s: %s", order_id, exc)
        return HttpResponse("Invalid order amount.", status=400)

    callback_url = settings.BASE_URL.rstrip("/") + f"/payment/stk_push_callback/?order_id={order.id}"

    try:
        response = cl.stk_push(
            phone_number,
            amount,
            account_reference=str(order.id),
            transaction_desc=f"Payment for Order {order.id}",
            callback_url=callback_url,
        )
    except Exception as e:
        logger.exception("STK Push initiation failed for order %s: %s", order.id, e)
        return HttpResponse(f"Payment initiation failed: {str(e)}", status=500)

    payment = Payment.objects.create(
        order=order,
        amount=Decimal(amount),
        status=Payment.STATUS_PENDING,
        transaction_date=timezone.now(),
    )

    logger.info(
        "STK Push initiated for order %s, payment id %s, response: %s",
        order.id,
        payment.id,
        response,
    )
    return render(
        request,
        "payment/payment_processing.html",
        {
            "order": order,
            "payment": payment,
            "daraja_response": response,
            "phone_number": phone_number,
        },
    )


from django.views.decorators.http import require_GET


@require_GET
def payment_status(request, order_id):
    """Return latest payment + order status for polling on processing page."""
    order = get_object_or_404(Order, id=order_id)
    payment = Payment.objects.filter(order=order).order_by("-id").first()

    payment_status_value = payment.status if payment else "NOT_FOUND"
    order_status_value = order.status
    is_paid = payment_status_value == Payment.STATUS_PAID or order_status_value in ("PAID", "SHIPPED", "DELIVERED")
    is_failed = payment_status_value == Payment.STATUS_FAILED or order_status_value in ("FAILED", "CANCELLED", "REFUNDED")

    return JsonResponse(
        {
            "order_id": order.id,
            "payment_status": payment_status_value,
            "order_status": order_status_value,
            "is_paid": is_paid,
            "is_failed": is_failed,
            "receipt_url": reverse("product:receipt", args=[order.id]),
        }
    )

# ---------------- Safaricom Callback ---------------- #
@csrf_exempt
def stk_push_callback(request):
    """Handle asynchronous STK Push callback from Safaricom."""
    if request.method != "POST":
        return HttpResponse("Only POST allowed", status=405)

    qs_order_id = request.GET.get("order_id")
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception as exc:
        logger.exception("Invalid JSON in STK callback: %s", exc)
        return HttpResponse("Invalid JSON", status=400)

    logger.info("📥 STK Callback payload: %s", json.dumps(payload))

    stk_callback = payload.get("Body", {}).get("stkCallback", {})
    result_code = stk_callback.get("ResultCode", -1)
    metadata = stk_callback.get("CallbackMetadata", {}).get("Item", [])

    # 🔎 Extract metadata
    mpesa_receipt, amount, phone = None, None, None
    for item in metadata:
        if item.get("Name") == "MpesaReceiptNumber":
            mpesa_receipt = item.get("Value")
        elif item.get("Name") == "Amount":
            amount = item.get("Value")
        elif item.get("Name") == "PhoneNumber":
            phone = item.get("Value")

    # 🔎 Locate order
    order = None
    if qs_order_id:
        order = Order.objects.filter(id=int(qs_order_id)).first()

    if not order and amount:
        candidate = Payment.objects.filter(
            status=Payment.STATUS_PENDING, amount=amount
        ).order_by("-id").first()
        if candidate:
            order = candidate.order

    if not order:
        logger.error("❌ Could not locate order for STK callback.")
        return JsonResponse({"ResultCode": 0, "ResultDesc": "Order not found, logged"})

    # 🔎 Get or create payment
    payment = Payment.objects.filter(order=order).order_by("-id").first()
    if not payment:
        payment = Payment.objects.create(
            order=order, amount=amount or order.total_price, status=Payment.STATUS_PENDING
        )

    # ⏳ Idempotency check
    if payment.status == Payment.STATUS_PAID and order.status in ("PAID", "SHIPPED", "DELIVERED"):
        logger.info("Duplicate STK callback ignored: order %s already processed", order.id)
        return JsonResponse({"ResultCode": 0, "ResultDesc": "Already processed"})

    try:
        with transaction.atomic():
            if int(result_code) == 0:
                # ✅ Mark payment as PAID
                payment.status = Payment.STATUS_PAID
                payment.mpesa_receipt_no = mpesa_receipt
                payment.transaction_date = timezone.now()
                payment.save()

                if order.status not in ("PAID", "SHIPPED", "DELIVERED"):
                    order.status = "PAID"
                    order.save(update_fields=["status"])

                    applied = apply_stock_deduction(
                        order, payment=payment, source=StockDeductionLog.AUTO
                    )
                    if applied:
                        logger.info("✅ Stock deduction applied for order %s via STK callback", order.id)

                # 📩 Queue confirmation (email + SMS) via Celery
                subject = f"Payment Confirmation for Order #{order.id}"
                amount_value = amount or order.total_price
                message = (
                    f"Dear Customer,\n\n"
                    f"We have received your payment of KES {amount_value:.2f} for Order #{order.id}.\n"
                    f"Mpesa Receipt: {mpesa_receipt}\n"
                    f"Status: PAID.\n\n"
                    f"Thank you for shopping with us!"
                )

                if getattr(order, "customer", None):
                    email = getattr(order.customer, "email", None)
                    if email:
                        send_email_task.delay(subject, message, email)

                if phone:
                    send_sms_task.delay(phone, message)

            else:
                # ❌ Mark failed
                payment.status = Payment.STATUS_FAILED
                payment.transaction_date = timezone.now()
                payment.save()

                if order.status not in ("PAID", "CANCELLED", "FAILED"):
                    order.status = "CANCELLED"
                    order.save()

    except Exception as exc:
        logger.exception("⚠️ Error processing STK callback for order %s: %s", order.id, exc)
        return JsonResponse({"ResultCode": 1, "ResultDesc": "Error processing callback"}, status=500)

    return JsonResponse({"ResultCode": 0, "ResultDesc": "Callback processed"})


# ---------------- Views for User Feedback ---------------- #
def payment_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, status="PAID")
    return render(request, "payment/payment_success.html", {"order": order})


def payment_failed(request, order_id):
    order = get_object_or_404(Order, id=order_id, status__in=["CANCELLED", "FAILED"])
    return render(request, "payment/payment_failed.html", {"order": order})


# ---------------- Order Cleanup ---------------- #
def unpaid_orders_cleanup():
    threshold = timezone.now() - timezone.timedelta(hours=72)
    stale_orders = Order.objects.filter(status="PENDING", created_at__lt=threshold)
    for order in stale_orders:
        order.status = "CANCELLED"
        order.save()
        Payment.objects.filter(order=order).update(status=Payment.STATUS_FAILED)
        logger.info("Auto-cancelled stale order %s", order.id)


# ---------------- Cancel Order ---------------- #
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.status = "CANCELLED"
    order.save()

    # Cancel all related payments
    Payment.objects.filter(order=order).update(status=Payment.STATUS_FAILED)

    return JsonResponse({"message": f"Order {order.id} has been cancelled."})
