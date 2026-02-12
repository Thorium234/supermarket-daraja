from django.core.paginator import Paginator

from product.repositories import ProductRepository
from product.services.image_service import UnsplashImageService


class ProductCatalogService:
    """Application service for catalog/search/listing logic."""

    @staticmethod
    def list_products(*, search=None, category=None, min_price=None, max_price=None, sort="newest", page=1, page_size=12, stock_only=False):
        queryset = ProductRepository.filtered_queryset(
            search=search,
            category_slug=category,
            min_price=min_price,
            max_price=max_price,
            stock_only=stock_only,
        )
        queryset = ProductRepository.with_catalog_annotations(queryset)
        queryset = ProductRepository.apply_sorting(queryset, sort)

        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        products = []
        for product in page_obj.object_list:
            image = UnsplashImageService.get_image_for_product(
                product_name=product.name,
                category_name=(product.category.name if product.category else None),
                uploaded_url=(product.image.url if product.image else None),
            )
            products.append(
                {
                    "id": product.id,
                    "name": product.name,
                    "description": product.description,
                    "price": float(product.price),
                    "discount_percentage": int(product.discount_percentage or 0),
                    "discounted_price": float(product.discounted_price),
                    "stock": product.stock,
                    "barcode": product.barcode,
                    "category": product.category.name if product.category else None,
                    "avg_rating": round(float(getattr(product, "avg_rating", 0) or 0), 2),
                    "review_count": int(getattr(product, "review_count", 0) or 0),
                    "popularity": int(getattr(product, "popularity", 0) or 0),
                    "image_url": image.image_url,
                    "image_source": image.source,
                }
            )

        return {
            "items": products,
            "pagination": {
                "page": page_obj.number,
                "pages": paginator.num_pages,
                "total": paginator.count,
                "has_next": page_obj.has_next(),
                "has_previous": page_obj.has_previous(),
            },
        }
