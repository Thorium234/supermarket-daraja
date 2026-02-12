from dataclasses import dataclass
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.core.cache import cache


CATEGORY_KEYWORDS = {
    "electronics": "electronics gadget product",
    "grocery": "fresh groceries supermarket",
    "fashion": "fashion apparel product",
    "beauty": "beauty skincare product",
    "home": "home appliance product",
    "default": "supermarket product",
}


@dataclass
class ImageResult:
    image_url: str
    source: str


class UnsplashImageService:
    """Fetch and cache relevant product images from Unsplash."""

    @staticmethod
    def _fallback_url():
        return f"{getattr(settings, 'STATIC_URL', '/static/').rstrip('/')}/product/img/fallback-product.svg"

    @staticmethod
    def _keyword_for(category_name, product_name):
        if category_name:
            normalized = category_name.strip().lower()
            for key, value in CATEGORY_KEYWORDS.items():
                if key in normalized:
                    return f"{product_name} {value}".strip()
        return f"{product_name} {CATEGORY_KEYWORDS['default']}".strip()

    @classmethod
    def get_image_for_product(cls, product_name, category_name=None, uploaded_url=None):
        if uploaded_url:
            return ImageResult(uploaded_url, "uploaded")

        access_key = getattr(settings, "UNSPLASH_ACCESS_KEY", "").strip()
        if not access_key:
            return ImageResult(cls._fallback_url(), "fallback")

        keyword = cls._keyword_for(category_name, product_name)
        cache_key = f"unsplash:image:{keyword.lower()}"
        cached = cache.get(cache_key)
        if cached:
            return ImageResult(cached, "cache")

        try:
            params = {
                "query": keyword,
                "per_page": 1,
                "orientation": "squarish",
                "content_filter": "high",
                "client_id": access_key,
            }
            endpoint = f"https://api.unsplash.com/search/photos?{urlencode(params)}"
            response = requests.get(endpoint, timeout=3)
            response.raise_for_status()
            payload = response.json()
            result = (payload.get("results") or [None])[0]
            if result and result.get("urls", {}).get("regular"):
                raw_url = result["urls"]["regular"]
                optimized_url = f"{raw_url}&w=600&h=600&fit=crop&auto=format&q=80"
                cache.set(cache_key, optimized_url, timeout=60 * 60 * 24)
                return ImageResult(optimized_url, "unsplash")
        except Exception:
            pass

        return ImageResult(cls._fallback_url(), "fallback")
