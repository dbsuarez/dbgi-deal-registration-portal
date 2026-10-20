import logging

from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404

from .models import RegistrationAttachment

logger = logging.getLogger(__name__)


def _can_access_registration(user, company_id):
    if user.is_dbgi_admin:
        return True
    return (
        user.role == user.Role.COMPANY and user.company_id == company_id and user.company.is_active
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
