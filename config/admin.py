import json
from datetime import timedelta
from io import BytesIO
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import FileResponse, Http404
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone
from unfold.sites import UnfoldAdminSite


class DBGIAdminSite(UnfoldAdminSite):
    index_template = "admin/operations_dashboard.html"

    def has_permission(self, request):
        user = request.user
        return bool(user.is_active and user.is_staff and user.is_dbgi_admin)

    def get_urls(self):
        return [
            path(
                "danger-zone/",
                self.admin_view(self.danger_zone_view),
                name="danger-zone",
            ),
            *super().get_urls(),
        ]

    def danger_zone_view(self, request):
        if not request.user.is_superuser:
            raise Http404

        from registrations.maintenance import (
            clear_transactional_records,
            transactional_record_counts,
        )
        from registrations.models import Registration
        from registrations.snapshots import (
            SnapshotError,
            delete_snapshot,
            export_snapshot,
            import_backup,
            list_snapshots,
            restore_snapshot,
            snapshots_available,
            take_snapshot,
        )

        confirmation_phrase = "DELETE ALL TRANSACTIONAL DATA"
        restore_phrase = "RESTORE SNAPSHOT"
        action = request.POST.get("action", "clear") if request.method == "POST" else ""
        if action in {"snapshot", "restore", "delete_snapshot", "download", "upload"}:
            if not snapshots_available():
                raise Http404
            name = request.POST.get("snapshot", "")
            if action == "download":
                try:
                    backup = BytesIO()
                    export_snapshot(name, backup)
                except SnapshotError as error:
                    raise Http404 from error
                backup.seek(0)
                return FileResponse(
                    backup, as_attachment=True, filename=f"dbgi-portal-backup-{name}.zip"
                )
            try:
                if action == "upload":
                    uploaded = request.FILES.get("backup")
                    if uploaded is None:
                        raise SnapshotError("Choose a backup file to upload.")
                    added = import_backup(uploaded)
                    log = (ADDITION, f"Uploaded backup as snapshot {added}", {"name": added})
                    messages.success(
                        request, "Backup uploaded. It is now in the list, ready to restore."
                    )
                elif action == "snapshot":
                    taken = take_snapshot(request.POST.get("label", ""))
                    log = (ADDITION, f"Snapshot {taken['name']}", taken)
                    messages.success(request, f"Snapshot taken: {taken['taken_at']}.")
                elif action == "delete_snapshot":
                    delete_snapshot(name)
                    log = None
                    messages.success(request, "Snapshot deleted.")
                elif request.POST.get("restore_confirmation", "").strip() != restore_phrase:
                    log = None
                    messages.error(request, f"Type {restore_phrase} exactly to restore.")
                else:
                    restored = restore_snapshot(name)
                    log = (CHANGE, f"Restored snapshot {name}", restored)
                    messages.success(request, f"Restored the snapshot from {restored['taken_at']}.")
            except SnapshotError as error:
                log = None
                messages.error(request, str(error))
            # After a restore the signed-in user may not exist any more, so log only if they do.
            if log and get_user_model().objects.filter(pk=request.user.pk).exists():
                LogEntry.objects.log_action(
                    user_id=request.user.pk,
                    content_type_id=ContentType.objects.get_for_model(Registration).pk,
                    object_id=None,
                    object_repr=log[1],
                    action_flag=log[0],
                    change_message=json.dumps(log[2]),
                )
        elif request.method == "POST":
            confirmation = request.POST.get("confirmation", "").strip()
            acknowledged = request.POST.get("acknowledge") == "on"
            if not acknowledged:
                messages.error(request, "Confirm that you understand this action cannot be undone.")
            elif confirmation != confirmation_phrase:
                messages.error(
                    request,
                    f"Type {confirmation_phrase} exactly to continue.",
                )
            else:
                counts = clear_transactional_records()
                LogEntry.objects.log_action(
                    user_id=request.user.pk,
                    content_type_id=ContentType.objects.get_for_model(Registration).pk,
                    object_id=None,
                    object_repr="All registration transactional data",
                    action_flag=DELETION,
                    change_message=json.dumps({"deleted": counts}),
                )
                messages.success(request, "All registration transactional data was deleted.")

        context = {
            **self.each_context(request),
            "title": "Danger Zone",
            "subtitle": "Irreversible superuser operations",
            "confirmation_phrase": confirmation_phrase,
            "restore_phrase": restore_phrase,
            "counts": transactional_record_counts(),
            "snapshots_available": snapshots_available(),
            "snapshots": list_snapshots() if snapshots_available() else [],
        }
        request.current_app = self.name
        return TemplateResponse(request, "admin/danger_zone.html", context)

    def index(self, request, extra_context=None):
        from registrations.models import (
            EndUser,
            Registration,
            RegistrationCategoryApproval,
            RegistrationNotification,
        )

        review_statuses = (
            Registration.Status.SUBMITTED,
            Registration.Status.RESUBMITTED,
            Registration.Status.REVIEW_REQUIRED,
            Registration.Status.UNDER_REVIEW,
        )
        review_queue = Registration.objects.filter(
            Q(status__in=review_statuses) | Q(needs_review=True)
        ).select_related("company")
        if not request.user.has_perm("registrations.view_registration"):
            review_queue = review_queue.none()
        pricing_queue = (
            RegistrationCategoryApproval.objects.filter(
                status__in=(
                    RegistrationCategoryApproval.Status.PENDING,
                    RegistrationCategoryApproval.Status.CHANGES_REQUESTED,
                )
            )
            .exclude(registration__status=Registration.Status.WITHDRAWN)
            .select_related("registration", "registration__company")
        )
        if not request.user.has_perm("registrations.view_registrationcategoryapproval"):
            pricing_queue = pricing_queue.none()
        pending_end_users = EndUser.objects.filter(status=EndUser.Status.PENDING)
        if not request.user.has_perm("registrations.view_enduser"):
            pending_end_users = pending_end_users.none()
        failed_notifications = RegistrationNotification.objects.filter(
            email_status=RegistrationNotification.EmailStatus.FAILED
        ).select_related("recipient", "registration")
        if not request.user.has_perm("registrations.view_registrationnotification"):
            failed_notifications = failed_notifications.none()
        expiring_approvals = RegistrationCategoryApproval.objects.filter(
            status=RegistrationCategoryApproval.Status.APPROVED,
            valid_until__gte=timezone.localdate(),
            valid_until__lte=timezone.localdate() + timedelta(days=30),
        ).select_related("registration", "registration__company")
        if not request.user.has_perm("registrations.view_registrationcategoryapproval"):
            expiring_approvals = expiring_approvals.none()

        dashboard_context = {
            "title": "Operations dashboard",
            "review_count": review_queue.count(),
            "pricing_count": pricing_queue.count(),
            "pending_end_user_count": pending_end_users.count(),
            "failed_notification_count": failed_notifications.count(),
            "expiring_approval_count": expiring_approvals.count(),
            "review_queue": review_queue.order_by("original_submitted_at", "id")[:5],
            "pricing_queue": pricing_queue.order_by("created_at", "id")[:5],
            "pending_end_users": pending_end_users.order_by("created_at", "id")[:5],
            "failed_notifications": failed_notifications.order_by("-created_at", "-id")[:5],
            "expiring_approvals": expiring_approvals.order_by("valid_until", "id")[:5],
            "registration_list_url": reverse("admin:registrations_registration_changelist"),
            "pricing_list_url": reverse(
                "admin:registrations_registrationcategoryapproval_changelist"
            ),
            "end_user_list_url": (
                f"{reverse('admin:registrations_enduser_changelist')}?"
                f"{urlencode({'status__exact': EndUser.Status.PENDING})}"
            ),
            "notification_list_url": reverse(
                "admin:registrations_registrationnotification_changelist"
            ),
            "danger_zone_url": (
                reverse("admin:danger-zone") if request.user.is_superuser else None
            ),
        }
        return super().index(request, {**dashboard_context, **(extra_context or {})})
