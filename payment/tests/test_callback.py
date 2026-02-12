# payment/tests/test_callback.py
import json
from django.test import TestCase, Client
from django.urls import reverse

from product.models import Order, OrderItem, Product
from payment.models import Payment

class STKCallbackTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.product = Product.objects.create(name="Test Product", stock=10, price=100)
        self.order = Order.objects.create(total_price=200, status="PENDING")
        OrderItem.objects.create(order=self.order, product=self.product, quantity=2)
        self.payment = Payment.objects.create(order=self.order, amount=200, status="PENDING")

        self.url = reverse("payment:stk_push_callback") + f"?order_id={self.order.id}"

    def _make_callback(self, result_code=0, receipt="XYZ123", amount=200, phone="254700000000"):
        """Helper to send a fake Safaricom callback"""
        payload = {
            "Body": {
                "stkCallback": {
                    "ResultCode": result_code,
                    "MerchantRequestID": "111",
                    "CheckoutRequestID": "222",
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "Amount", "Value": amount},
                            {"Name": "MpesaReceiptNumber", "Value": receipt},
                            {"Name": "PhoneNumber", "Value": phone},
                        ]
                    },
                }
            }
        }
        return self.client.post(self.url, data=json.dumps(payload), content_type="application/json")

    def test_successful_payment_marks_order_paid_and_reduces_stock(self):
        response = self._make_callback(result_code=0)
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.product.refresh_from_db()
        self.payment.refresh_from_db()
        self.assertEqual(self.order.status, "PAID")
        self.assertEqual(self.payment.status, "PAID")
        self.assertEqual(self.product.stock, 8)  # 10 - 2

    def test_failed_payment_marks_order_cancelled(self):
        response = self._make_callback(result_code=1)
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.payment.refresh_from_db()
        self.assertEqual(self.order.status, "CANCELLED")
        self.assertEqual(self.payment.status, "FAILED")

    def test_idempotency_duplicate_callback_does_not_double_deduct(self):
        self._make_callback(result_code=0)
        self.product.refresh_from_db()
        stock_after_first = self.product.stock
        # Call again
        self._make_callback(result_code=0)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, stock_after_first)  # no further deduction
