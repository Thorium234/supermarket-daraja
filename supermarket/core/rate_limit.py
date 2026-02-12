import time
from functools import wraps
from django.core.cache import cache
from .responses import api_error


def rate_limit(key_prefix="api", limit=60, window_seconds=60):
    """Simple fixed-window per-IP limiter for API endpoints."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", "unknown")).split(",")[0].strip()
            bucket = int(time.time() // window_seconds)
            cache_key = f"rl:{key_prefix}:{ip}:{bucket}"
            try:
                current = cache.incr(cache_key)
            except ValueError:
                cache.set(cache_key, 1, timeout=window_seconds)
                current = 1

            if current > limit:
                return api_error("Rate limit exceeded", status=429)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
