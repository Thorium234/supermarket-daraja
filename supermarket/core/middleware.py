from django.http import JsonResponse


class ApiExceptionMiddleware:
    """Catch unhandled API exceptions and return consistent JSON."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/api/") and request.method == "OPTIONS":
            response = JsonResponse({"ok": True, "message": "preflight"})
            response["Access-Control-Allow-Origin"] = "*"
            response["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
            response["Access-Control-Allow-Methods"] = "GET, POST, PATCH, DELETE, OPTIONS"
            return response

        try:
            response = self.get_response(request)
            if request.path.startswith("/api/"):
                response["Access-Control-Allow-Origin"] = "*"
                response["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
                response["Access-Control-Allow-Methods"] = "GET, POST, PATCH, DELETE, OPTIONS"
            return response
        except Exception as exc:
            if request.path.startswith("/api/"):
                return JsonResponse({"ok": False, "message": "Internal server error", "detail": str(exc)}, status=500)
            raise
