import logging

from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404

from .models import ProjectOutcomeReport, RegistrationAttachment, RepeatOrder

logger = logging.getLogger(__name__)

# Files the browser can show in the preview box. Word and Excel files are only downloaded.
PREVIEW_TYPES = {
    "pdf": "application/pdf",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
}


def _can_access_registration(user, company_id):
    if user.is_dbgi_admin:
        return True
    return (
        user.role == user.Role.COMPANY and user.company_id == company_id and user.company.is_active
    )


def _file_response(request, stored, name):
    """Send a private file. With ?inline=1, a PDF or picture opens in the browser's preview box
    (same site only); everything else, and every other request, is a download."""
    extension = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if request.GET.get("inline") == "1" and extension in PREVIEW_TYPES:
        response = FileResponse(
            stored.open("rb"),
            as_attachment=False,
            filename=name,
            content_type=PREVIEW_TYPES[extension],
        )
        # The portal shows it inside its own page; other sites still cannot frame it.
        response["X-Frame-Options"] = "SAMEORIGIN"
    else:
        response = FileResponse(
            stored.open("rb"),
            as_attachment=True,
            filename=name,
            content_type="application/octet-stream",
        )
    response["Cache-Control"] = "private, no-store"
    return response


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
    return _file_response(request, attachment.file, attachment.original_name)


@login_required
def repeat_order_letter(request, repeat_order_id, letter):
    repeat_order = get_object_or_404(
        RepeatOrder.objects.select_related("registration"), pk=repeat_order_id
    )
    if letter not in {"noa", "ntp"}:
        raise Http404
    if not _can_access_registration(request.user, repeat_order.registration.company_id):
        raise Http404
    stored, name = (
        (repeat_order.noa_file, repeat_order.noa_name)
        if letter == "noa"
        else (repeat_order.ntp_file, repeat_order.ntp_name)
    )
    if not stored.storage.exists(stored.name):
        logger.error("Repeat order letter is missing", extra={"repeat_order_id": repeat_order.pk})
        raise Http404("The letter is unavailable.")
    return _file_response(request, stored, name)


@login_required
def outcome_award_notice(request, report_id):
    """The Notice of Award attached to a Won report: for that company and DBGI only."""
    report = get_object_or_404(
        ProjectOutcomeReport.objects.select_related("registration"), pk=report_id
    )
    if not report.award_notice or not _can_access_registration(
        request.user, report.registration.company_id
    ):
        raise Http404
    stored = report.award_notice
    if not stored.storage.exists(stored.name):
        logger.error("Notice of Award is missing", extra={"outcome_report_id": report.pk})
        raise Http404("The Notice of Award is unavailable.")
    return _file_response(request, stored, report.award_notice_name)
