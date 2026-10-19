from urllib.parse import urlencode

from django.shortcuts import redirect
from django.urls import reverse


class DBGIAdminAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        admin_login_path = reverse("admin:login")
        if (
            request.path.startswith("/admin/")
            and request.path != admin_login_path
            and request.user.is_authenticated
            and not request.user.is_dbgi_admin
        ):
            query = urlencode({"next": request.get_full_path()})
            return redirect(f"{admin_login_path}?{query}")
        return self.get_response(request)
