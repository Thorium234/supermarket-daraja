from django.http import JsonResponse
import json


def parse_json_body(request):
    try:
        return json.loads((request.body or b"{}").decode("utf-8"))
    except Exception:
        return None


def api_success(data=None, message="OK", status=200):
    return JsonResponse({"ok": True, "message": message, "data": data or {}}, status=status)


def api_error(message="Bad request", status=400, errors=None):
    payload = {"ok": False, "message": message}
    if errors:
        payload["errors"] = errors
    return JsonResponse(payload, status=status)
