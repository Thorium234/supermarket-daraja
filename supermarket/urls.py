from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("product.urls")),   # customer & admin supermarket logic
    path("api/", include("product.api.urls")),
    path("payment/", include("payment.urls")),  # mpesa integration
    path("accounts/", include("django.contrib.auth.urls")),
    path("qr-code/", include("qr_code.urls", namespace="qr_code")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
