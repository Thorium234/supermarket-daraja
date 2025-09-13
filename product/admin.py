# product/admin.py
from django.contrib import admin
from .models import Shelf, Product, Customer, Order, OrderItem, VerificationLog


@admin.register(Shelf)
class ShelfAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "description")
    search_fields = ("name", "location")
    ordering = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "stock", "shelf", "barcode", "created_at")
    search_fields = ("name", "barcode", "shelf__name")
    list_filter = ("created_at", "shelf")
    autocomplete_fields = ("shelf",)


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
    search_fields = ("customer__phone_number", "receipt_number")
    inlines = [OrderItemInline]


@admin.register(VerificationLog)
class VerificationLogAdmin(admin.ModelAdmin):
    list_display = ("order", "verified_at", "ip_address", "verified_by")
    list_filter = ("verified_at", "verified_by")
    search_fields = ("order__id", "ip_address", "user_agent")


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

# Make sure groups (Cashier / Owner) exist
def ensure_default_groups():
    for group_name in ["Cashier", "Owner"]:
        Group.objects.get_or_create(name=group_name)

ensure_default_groups()
