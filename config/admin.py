import json
from datetime import timedelta
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.admin.models import DELETION, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import Http404
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

        confirmation_phrase = "DELETE ALL TRANSACTIONAL DATA"
        if request.method == "POST":
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
            "counts": transactional_record_counts(),
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
        pricing_queue = RegistrationCategoryApproval.objects.filter(
            status__in=(
                RegistrationCategoryApproval.Status.PENDING,
                RegistrationCategoryApproval.Status.CHANGES_REQUESTED,
            )
        ).select_related("registration", "registration__company")
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
