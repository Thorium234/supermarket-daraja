"""Lightweight serializer helpers for JSON API payloads."""


def serialize_product(product):
    image_url = product.image.url if getattr(product, "image", None) else getattr(product, "dynamic_image_url", None)
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": float(product.price),
        "discount_percentage": product.discount_percentage,
        "discounted_price": float(product.discounted_price),
        "stock": product.stock,
        "barcode": product.barcode,
        "category": product.category.name if getattr(product, "category", None) else None,
        "image_url": image_url,
        "avg_rating": float(getattr(product, "avg_rating", 0) or 0),
        "reviews_count": int(getattr(product, "reviews_count", 0) or 0),
    }


def serialize_review(review):
    return {
        "id": review.id,
        "rating": review.rating,
        "comment": review.comment,
        "customer": review.customer.name or review.customer.phone_number,
        "created_at": review.created_at.isoformat(),
    }
