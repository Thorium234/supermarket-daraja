from django.urls import path
from . import views

app_name = "product_api"

urlpatterns = [
    path("auth/register/", views.auth_register_api, name="auth_register_api"),
    path("auth/login/", views.auth_login_api, name="auth_login_api"),

    path("products/", views.product_list_api, name="product_list_api"),
    path("categories/", views.category_list_api, name="category_list_api"),
    path("products/<int:product_id>/", views.product_detail_api, name="product_detail_api"),
    path("products/<int:product_id>/reviews/", views.review_create_api, name="review_create_api"),

    path("orders/", views.order_create_api, name="order_create_api"),
    path("orders/history/", views.order_history_api, name="order_history_api"),

    path("admin/products/", views.admin_product_create_api, name="admin_product_create_api"),
]
