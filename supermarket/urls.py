from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("product.urls")),   # customer & admin supermarket logic
    path("payment/", include("payment.urls")),  # mpesa integration
    path("accounts/", include("django.contrib.auth.urls")),
    path("qr-code/", include("qr_code.urls", namespace="qr_code")),
]
