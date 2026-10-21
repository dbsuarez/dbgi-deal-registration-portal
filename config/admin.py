from datetime import timedelta

from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from unfold.sites import UnfoldAdminSite


class DBGIAdminSite(UnfoldAdminSite):
    index_template = "admin/operations_dashboard.html"

    def has_permission(self, request):
        user = request.user
        return bool(user.is_active and user.is_staff and user.is_dbgi_admin)

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
            "end_user_list_url": reverse("admin:registrations_enduser_changelist"),
            "notification_list_url": reverse(
                "admin:registrations_registrationnotification_changelist"
            ),
        }
        return super().index(request, {**dashboard_context, **(extra_context or {})})
