import logging

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .models import RegistrationAttachment, User

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


def _can_access_registration(user, company_id):
    if user.is_dbgi_admin:
        return True
    return (
        user.role == user.Role.COMPANY
        and user.company_id == company_id
        and user.company.is_active
    )


@login_required
def registration_attachment(request, attachment_id):
    attachment = get_object_or_404(
        RegistrationAttachment.objects.select_related("registration"),
        pk=attachment_id,
    )
    if not _can_access_registration(request.user, attachment.registration.company_id):
        raise Http404
    if not attachment.file.storage.exists(attachment.file.name):
        logger.error(
            "Registration attachment file is missing",
            extra={
                "attachment_id": attachment.pk,
                "registration_id": attachment.registration_id,
            },
        )
        raise Http404("Attachment file is unavailable.")
    response = FileResponse(
        attachment.file.open("rb"),
        as_attachment=True,
        filename=attachment.original_name,
        content_type="application/octet-stream",
    )
    response["Cache-Control"] = "private, no-store"
    return response
