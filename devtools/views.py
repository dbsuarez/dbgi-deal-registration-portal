import logging

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from registrations.models import User

logger = logging.getLogger(__name__)


class DevelopmentLoginView(LoginView):
    template_name = "registration/login.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if settings.DEBUG:
            users = User.objects.filter(is_active=True).select_related("company").order_by(
                "company__name", "username"
            )
            context["development_company_users"] = [
                user for user in users if not user.is_dbgi_admin
            ]
            context["development_admin_users"] = [
                user for user in users if user.is_dbgi_admin
            ]
        return context


@require_POST
def development_login(request):
    if not settings.DEBUG:
        raise Http404
    user = get_object_or_404(User, username=request.POST.get("username", ""), is_active=True)
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    logger.info("Development login used", extra={"user_id": user.pk})
    requested_next = request.POST.get("next", "")
    if requested_next and url_has_allowed_host_and_scheme(
        requested_next,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(requested_next)
    return redirect("/")
