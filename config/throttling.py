import hashlib
import logging
import time
from dataclasses import dataclass

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ThrottlePolicy:
    scope: str
    identity: str
    limit: int
    window_seconds: int
    api_response: bool


def _request_identity(request):
    if request.user.is_authenticated:
        return f"user:{request.user.pk}"
    return f"address:{request.META.get('REMOTE_ADDR', 'unknown')}"


def _login_identity(request):
    username = " ".join(request.POST.get("username", "").casefold().split())
    return f"username:{username}" if username else _request_identity(request)


def _policy_for(request):
    if request.method != "POST" and request.method not in {"PUT", "PATCH", "DELETE"}:
        return None
    if request.path in {"/accounts/login/", "/accounts/debug-login/", "/admin/login/"}:
        return ThrottlePolicy(
            scope="login",
            identity=_login_identity(request),
            limit=settings.LOGIN_THROTTLE_LIMIT,
            window_seconds=settings.LOGIN_THROTTLE_WINDOW_SECONDS,
            api_response=False,
        )
    if request.path.startswith("/api/v1/"):
        return ThrottlePolicy(
            scope="api-mutation",
            identity=_request_identity(request),
            limit=settings.API_MUTATION_THROTTLE_LIMIT,
            window_seconds=settings.API_MUTATION_THROTTLE_WINDOW_SECONDS,
            api_response=True,
        )
    return None


def _consume(policy):
    now = int(time.time())
    window = now // policy.window_seconds
    identity_hash = hashlib.sha256(policy.identity.encode()).hexdigest()
    key = f"throttle:{policy.scope}:{identity_hash}:{window}"
    timeout = policy.window_seconds + 1
    if cache.add(key, 1, timeout=timeout):
        count = 1
    else:
        try:
            count = cache.incr(key)
        except ValueError:
            cache.add(key, 1, timeout=timeout)
            count = 1
    retry_after = policy.window_seconds - (now % policy.window_seconds)
    return count, retry_after


def _limited_response(policy, retry_after):
    message = "Too many requests. Wait before trying again."
    if policy.api_response:
        response = JsonResponse(
            {
                "code": "rate_limited",
                "message": message,
                "details": [],
            },
            status=429,
        )
    else:
        response = HttpResponse(message, status=429, content_type="text/plain; charset=utf-8")
    response["Retry-After"] = str(retry_after)
    response["X-RateLimit-Limit"] = str(policy.limit)
    response["X-RateLimit-Remaining"] = "0"
    return response


class RequestThrottleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not settings.THROTTLE_ENABLED:
            return self.get_response(request)
        policy = _policy_for(request)
        if not policy:
            return self.get_response(request)
        try:
            count, retry_after = _consume(policy)
        except Exception:
            logger.exception("Request throttle backend failed")
            if settings.THROTTLE_FAIL_CLOSED:
                return JsonResponse(
                    {
                        "code": "service_unavailable",
                        "message": "The request cannot be processed safely right now.",
                        "details": [],
                    },
                    status=503,
                )
            return self.get_response(request)
        if count > policy.limit:
            return _limited_response(policy, retry_after)
        response = self.get_response(request)
        response["X-RateLimit-Limit"] = str(policy.limit)
        response["X-RateLimit-Remaining"] = str(max(policy.limit - count, 0))
        return response
