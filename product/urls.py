from django.urls import path
from . import views

app_name = "product"

urlpatterns = [
    # ---------------- Public / Shop ---------------- #
    path("", views.product_list, name="product_list"),

    # ---------------- Cart ---------------- #
    path("cart/", views.cart_view, name="cart"),
    path("cart/count/", views.cart_count_ajax, name="cart_count_ajax"),
    path("cart/add/<int:pk>/", views.add_to_cart, name="add_to_cart"),
    path("cart/remove/<int:pk>/", views.remove_from_cart, name="remove_from_cart"),
    path("cart/update/<int:pk>/", views.update_cart, name="update_cart"),
    path("cart/clear/", views.clear_cart, name="clear_cart"),

    # ---------------- Checkout & Orders ---------------- #
    path("checkout/", views.checkout, name="checkout"),
    path("order/<int:order_id>/verify/", views.verify_order, name="verify_order"),
    path("order/<int:order_id>/check-status/", views.check_payment_status, name="check_payment_status"),
    path("order/<int:order_id>/paid/", views.mark_order_paid, name="mark_order_paid"),

    # ---------------- Receipts ---------------- #
    path("receipt/<int:order_id>/", views.receipt, name="receipt"),
    path("receipt/<int:order_id>/pdf/", views.receipt_pdf, name="receipt_pdf"),
    path("receipt-view/<int:order_id>/", views.receipt_view, name="receipt_view"),
    path("receipt/<int:order_id>/send-sms/", views.send_receipt_sms, name="send_receipt_sms"),
    path("receipt/<int:order_id>/verify/", views.verify_order, name="receipt_verify"),

    # ---------------- Admin / Cashier ---------------- #
    path("dashboard/", views.dashboard, name="dashboard"),

    # Products management
    path("dashboard/products/", views.product_list_admin, name="product_list_admin"),
    path("dashboard/products/create/", views.product_create, name="product_create"),
    path("dashboard/products/<int:pk>/edit/", views.product_edit, name="product_edit"),
    path("dashboard/products/<int:pk>/delete/", views.product_delete, name="product_delete"),

    # Reports & Graphs
    path("dashboard/export/excel/", views.export_excel, name="export_excel"),
    path("dashboard/sales-graph/", views.sales_graph, name="sales_graph"),
]

