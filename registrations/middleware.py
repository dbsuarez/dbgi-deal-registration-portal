from django.http import HttpResponseForbidden


class DBGIAdminAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.path.startswith("/admin/")
            and request.user.is_authenticated
            and not request.user.is_dbgi_admin
        ):
            return HttpResponseForbidden("DBGI administrator access required.")
        return self.get_response(request)
