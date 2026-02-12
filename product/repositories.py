from django.db.models import Q, Avg, Count, Sum
from django.db.models.functions import Coalesce

from .models import Product


class ProductRepository:
    """Data-access abstraction for product catalog queries."""

    @staticmethod
    def base_queryset():
        return Product.objects.select_related("category", "shelf").all()

    @classmethod
    def filtered_queryset(cls, *, search=None, category_slug=None, min_price=None, max_price=None, stock_only=False):
        queryset = cls.base_queryset()

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(description__icontains=search)
                | Q(barcode__icontains=search)
            )

        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)

        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)

        if stock_only:
            queryset = queryset.filter(stock__gt=0)

        return queryset

    @staticmethod
    def with_catalog_annotations(queryset):
        return queryset.annotate(
            avg_rating=Coalesce(Avg("reviews__rating"), 0.0),
            review_count=Coalesce(Count("reviews"), 0),
            popularity=Coalesce(Sum("orderitem__quantity"), 0),
        )

    @staticmethod
    def apply_sorting(queryset, sort):
        sort_map = {
            "price_asc": "price",
            "price_desc": "-price",
            "newest": "-created_at",
            "popularity": "-popularity",
            "rating": "-avg_rating",
            "name": "name",
        }
        return queryset.order_by(sort_map.get(sort, "-created_at"))
