from django.urls import path

from . import views

app_name = "owner"

urlpatterns = [
    path("", views.DashboardOverviewView.as_view(), name="dashboard"),
    path("products/", views.ProductListView.as_view(), name="product_list"),
    path("products/create/", views.ProductCreateView.as_view(), name="product_create"),
    path("products/<int:pk>/edit/", views.ProductUpdateView.as_view(), name="product_edit"),
    path("products/<int:pk>/delete/", views.ProductDeleteView.as_view(), name="product_delete"),
    path("categories/", views.CategoryListCreateView.as_view(), name="category_list"),
    path("orders/", views.OrderListView.as_view(), name="order_list"),
    path("orders/<int:pk>/", views.OrderDetailView.as_view(), name="order_detail"),
    path("customers/", views.CustomerListView.as_view(), name="customer_list"),
    path("customers/<int:pk>/", views.CustomerDetailView.as_view(), name="customer_detail"),
    path("reviews/", views.ReviewListView.as_view(), name="review_list"),
    path("reviews/<int:pk>/delete/", views.ReviewDeleteView.as_view(), name="review_delete"),
    path("analytics/", views.AnalyticsView.as_view(), name="analytics"),
]
