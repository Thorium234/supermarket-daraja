import datetime
from functools import wraps
import jwt
from django.conf import settings
from django.contrib.auth.models import User
from .responses import api_error


JWT_ALGORITHM = "HS256"
JWT_EXP_MINUTES = 60 * 12


def _jwt_secret():
    return settings.SECRET_KEY


def create_access_token(user):
    now = datetime.datetime.utcnow()
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "is_staff": user.is_staff,
        "iat": now,
        "exp": now + datetime.timedelta(minutes=JWT_EXP_MINUTES),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=JWT_ALGORITHM)


def decode_token(raw_token):
    return jwt.decode(raw_token, _jwt_secret(), algorithms=[JWT_ALGORITHM])


def get_bearer_token(request):
    header = request.META.get("HTTP_AUTHORIZATION", "")
    if not header.startswith("Bearer "):
        return None
    return header.replace("Bearer ", "", 1).strip()


def jwt_required(staff_only=False):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            token = get_bearer_token(request)
            if not token:
                return api_error("Missing Bearer token", status=401)
            try:
                payload = decode_token(token)
                user = User.objects.get(id=int(payload["sub"]), is_active=True)
            except jwt.ExpiredSignatureError:
                return api_error("Token expired", status=401)
            except Exception:
                return api_error("Invalid token", status=401)

            if staff_only and not (user.is_staff or user.is_superuser):
                return api_error("Forbidden", status=403)

            request.api_user = user
            request.api_token_payload = payload
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
