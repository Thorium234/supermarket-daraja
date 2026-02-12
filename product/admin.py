# product/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Shelf,
    Category,
    Product,
    Customer,
    Order,
    OrderItem,
    VerificationLog,
    ProductReview,
    Cart,
    CartItem,
)


@admin.register(Shelf)
class ShelfAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "description")
    search_fields = ("name", "location")
    ordering = ("name",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "created_at")
    search_fields = ("name", "slug")
    list_filter = ("is_active", "created_at")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "image_preview",
        "name",
        "category",
        "price",
        "discount_percentage",
        "stock",
        "is_active",
        "shelf",
        "barcode",
        "created_at",
    )
    search_fields = ("name", "barcode", "shelf__name", "category__name")
    list_filter = ("created_at", "shelf", "category", "is_active")
    autocomplete_fields = ("shelf", "category")

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width:36px;height:36px;object-fit:cover;border-radius:6px;" />', obj.image.url)
        return "No image"
    image_preview.short_description = "Image"


class OrderItemInline(admin.TabularInline):
    """Inline view of items inside an order."""
    model = OrderItem
    extra = 0
    readonly_fields = ("subtotal",)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "phone_number", "email", "created_at")
    search_fields = ("name", "phone_number", "email")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin): 
    list_display = ("id", "customer", "total_price", "status", "created_at", "stock_deducted")
    list_filter = ("status", "created_at")
    search_fields = ("customer__phone_number", "customer_name", "id")
    inlines = [OrderItemInline]


@admin.register(VerificationLog)
class VerificationLogAdmin(admin.ModelAdmin):
    list_display = ("order", "verified_at", "ip_address", "verified_by")
    list_filter = ("verified_at", "verified_by")
    search_fields = ("order__id", "ip_address", "user_agent")


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "customer", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("product__name", "customer__phone_number", "comment")


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "updated_at")
    search_fields = ("customer__phone_number", "customer__name")
    list_filter = ("updated_at",)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("cart", "product", "quantity", "created_at")
    search_fields = ("cart__customer__phone_number", "product__name")
    list_filter = ("created_at",)


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Group

# Unregister the original User admin
admin.site.unregister(User)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Extend UserAdmin to show groups and role assignment in the admin."""
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "get_roles")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")

    def get_roles(self, obj):
        return ", ".join([g.name for g in obj.groups.all()])
    get_roles.short_description = "Roles (Groups)"
