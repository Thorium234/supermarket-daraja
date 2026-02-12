import json
from datetime import timedelta

from django.db.models import Count, F, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from payment.models import Payment
from product.models import Category, Customer, Order, OrderItem, Product


class OwnerAnalyticsService:
    @staticmethod
    def _period_start(period: str):
        today = timezone.now().date()
        if period == "today":
            return today
        if period == "week":
            return today - timedelta(days=7)
        return today - timedelta(days=30)

    @classmethod
    def overview_metrics(cls, period: str = "month"):
        start_date = cls._period_start(period)
        orders = Order.objects.filter(created_at__date__gte=start_date)
        paid_orders = orders.filter(status__in=["PAID", "SHIPPED", "DELIVERED"])

        revenue = paid_orders.aggregate(total=Sum("total_price"))["total"] or 0
        low_stock = Product.objects.filter(stock__lte=5, is_active=True).order_by("stock", "name")[:8]

        return {
            "period": period,
            "total_products": Product.objects.filter(is_active=True).count(),
            "total_orders": orders.count(),
            "paid_orders": paid_orders.count(),
            "pending_orders": orders.filter(status="PENDING").count(),
            "failed_orders": orders.filter(status__in=["FAILED", "CANCELLED"]).count(),
            "revenue": revenue,
            "recent_orders": orders.select_related("customer").prefetch_related("items")[:10],
            "low_stock": low_stock,
        }

    @staticmethod
    def sales_trend(days: int = 14):
        start_date = timezone.now().date() - timedelta(days=days - 1)
        rows = (
            Order.objects.filter(status__in=["PAID", "SHIPPED", "DELIVERED"], created_at__date__gte=start_date)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(total=Sum("total_price"))
            .order_by("day")
        )
        by_day = {row["day"].isoformat(): float(row["total"] or 0) for row in rows}

        labels = []
        totals = []
        for i in range(days):
            day = start_date + timedelta(days=i)
            key = day.isoformat()
            labels.append(key)
            totals.append(by_day.get(key, 0.0))

        return {"labels": labels, "totals": totals}

    @staticmethod
    def top_products(limit: int = 5):
        rows = (
            OrderItem.objects.filter(order__status__in=["PAID", "SHIPPED", "DELIVERED"])
            .values("product__name")
            .annotate(total_sold=Sum("quantity"))
            .order_by("-total_sold")[:limit]
        )
        return [{"name": row["product__name"], "total_sold": row["total_sold"]} for row in rows]

    @staticmethod
    def revenue_by_category(limit: int = 8):
        rows = (
            OrderItem.objects.filter(order__status__in=["PAID", "SHIPPED", "DELIVERED"])
            .values("product__category__name")
            .annotate(revenue=Sum(F("price") * F("quantity")))
            .order_by("-revenue")[:limit]
        )
        return [
            {
                "category": row["product__category__name"] or "Uncategorized",
                "revenue": float(row["revenue"] or 0),
            }
            for row in rows
        ]

    @classmethod
    def chart_payloads(cls):
        trend = cls.sales_trend(days=14)
        top = cls.top_products(limit=6)
        by_category = cls.revenue_by_category(limit=6)
        payment_split = {
            "paid": Payment.objects.filter(status="PAID").count(),
            "pending": Payment.objects.filter(status="PENDING").count(),
            "failed": Payment.objects.filter(status="FAILED").count(),
            "refunded": Payment.objects.filter(status="REFUNDED").count(),
        }
        return {
            "sales_trend": json.dumps(trend),
            "top_products": json.dumps(top),
            "by_category": json.dumps(by_category),
            "payment_split": json.dumps(payment_split),
        }


class OwnerQueryService:
    @staticmethod
    def product_queryset(search: str = "", category: str = ""):
        queryset = Product.objects.select_related("category", "shelf").order_by("-created_at")
        if search:
            queryset = queryset.filter(name__icontains=search)
        if category:
            queryset = queryset.filter(category__slug=category)
        return queryset

    @staticmethod
    def order_queryset(status: str = ""):
        queryset = Order.objects.select_related("customer").prefetch_related("items__product").order_by("-created_at")
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    @staticmethod
    def customer_queryset(search: str = ""):
        queryset = Customer.objects.annotate(total_orders=Count("order"))
        if search:
            queryset = queryset.filter(phone_number__icontains=search)
        return queryset.order_by("-created_at")

    @staticmethod
    def categories_queryset():
        return Category.objects.annotate(total_products=Count("products")).order_by("name")
