from django.urls import path
from . import views

app_name = "payment"

urlpatterns = [
    # ---------------- Payment initiation + callbacks ---------------- #
    path("initiate-payment/<int:order_id>/", views.initiate_payment, name="initiate_payment"),
    path("status/<int:order_id>/", views.payment_status, name="payment_status"),
    path("stk_push_callback/", views.stk_push_callback, name="stk_push_callback"),

    # ---------------- Payment status feedback ---------------- #
    path("success/<int:order_id>/", views.payment_success, name="payment_success"),
    path("failed/<int:order_id>/", views.payment_failed, name="payment_failed"),

    # ---------------- Order actions ---------------- #
    path("cancel/<int:order_id>/", views.cancel_order, name="cancel_order"),
]
