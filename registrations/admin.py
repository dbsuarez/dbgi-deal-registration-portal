from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.db.models import F, OuterRef, Subquery, Window
from django.db.models.functions import Rank
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .audit import registration_snapshot
from .models import (
    Company,
    CompetitorItem,
    EndUser,
    EndUserAlias,
    MatchingSuggestion,
    Opportunity,
    OpportunityRanking,
    OpportunityScope,
    PriceApprovalRenewal,
    Product,
    Registration,
    RegistrationAttachment,
    RegistrationCategoryApproval,
    RegistrationEvent,
    RegistrationItem,
    RegistrationItemApproval,
    RegistrationReviewDecision,
    User,
)


@admin.register(Company)
class CompanyAdmin(ModelAdmin):
    list_display = ("name", "partner_code", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "partner_code")


@admin.register(User)
class PortalUserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    fieldsets = (*BaseUserAdmin.fieldsets, ("Portal access", {"fields": ("company", "role")}))
    add_fieldsets = (
        *BaseUserAdmin.add_fieldsets,
        (
            "Portal access",
            {"fields": ("company", "role", "is_staff", "is_superuser", "is_active")},
        ),
    )
    list_display = ("username", "email", "company", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active", "company")
    search_fields = ("username", "email", "company__name")


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ("code", "name", "category", "currency", "list_price", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("code", "name", "category")


class EndUserAliasInline(TabularInline):
    model = EndUserAlias
    extra = 0


@admin.register(EndUser)
class EndUserAdmin(ModelAdmin):
    list_display = (
        "official_name",
        "acronym",
        "city_municipality",
        "status",
        "proposed_by_company",
        "is_active",
        "updated_at",
    )
    list_filter = ("status", "is_active", "government_branch", "region", "province")
    search_fields = (
        "official_name",
        "acronym",
        "aliases__name",
        "city_municipality",
        "province",
        "philgeps_reference",
    )
    readonly_fields = (
        "normalized_name",
        "normalized_address",
        "proposed_by_company",
        "created_by",
        "verified_by",
        "verified_at",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        ("Identity", {"fields": ("official_name", "acronym", "parent", "status", "is_active")}),
        (
            "Organization classification",
            {"fields": ("government_branch", "organization_type", "sector")},
        ),
        (
            "Address",
            {
                "fields": (
                    "region",
                    "province",
                    "city_municipality",
                    "street_address",
                    "postal_code",
                )
            },
        ),
        ("Source", {"fields": ("philgeps_reference", "source_url")}),
        (
            "Audit",
            {
                "classes": ("collapse",),
                "fields": (
                    "proposed_by_company",
                    "created_by",
                    "verified_by",
                    "verified_at",
                    "normalized_name",
                    "normalized_address",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )
    inlines = (EndUserAliasInline,)
    actions = ("verify_selected", "archive_selected", "restore_selected")

    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.created_by_id:
            obj.created_by = request.user
        if obj.status == EndUser.Status.VERIFIED and not obj.verified_at:
            obj.verified_by = request.user
            obj.verified_at = timezone.now()
        elif obj.status != EndUser.Status.VERIFIED:
            obj.verified_by = None
            obj.verified_at = None
        super().save_model(request, obj, form, change)

    @admin.action(description="Verify selected End-users")
    def verify_selected(self, request, queryset):
        queryset.update(
            status=EndUser.Status.VERIFIED, verified_by=request.user, verified_at=timezone.now()
        )

    @admin.action(description="Archive selected End-users")
    def archive_selected(self, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description="Restore selected End-users")
    def restore_selected(self, request, queryset):
        queryset.update(is_active=True)


class OpportunityScopeInline(TabularInline):
    model = OpportunityScope
    extra = 0


@admin.register(Opportunity)
class OpportunityAdmin(ModelAdmin):
    list_display = ("title", "end_user_name", "project_status", "is_active", "created_at")
    list_filter = ("project_status", "is_active")
    search_fields = ("title", "end_user_name", "end_user_address")
    readonly_fields = ("created_by", "created_at")
    inlines = (OpportunityScopeInline,)

    def save_model(self, request, obj, form, change):
        previous_status = None
        if change:
            previous_status = self.get_queryset(request).get(pk=obj.pk).project_status
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
        if change and previous_status != obj.project_status:
            for registration in Registration.objects.filter(opportunity_scope__opportunity=obj):
                RegistrationEvent.objects.create(
                    registration=registration,
                    actor=request.user,
                    event_type="Project status changed",
                    details=(
                        f"Project status changed from {previous_status} to "
                        f"{obj.get_project_status_display()} through Django administration."
                    ),
                    snapshot=registration_snapshot(registration),
                )


class CompetitorItemInline(TabularInline):
    model = CompetitorItem
    extra = 0


class RegistrationItemInline(TabularInline):
    model = RegistrationItem
    extra = 0


class RegistrationEventInline(TabularInline):
    model = RegistrationEvent
    extra = 0
    can_delete = False
    readonly_fields = ("actor", "event_type", "details", "snapshot", "created_at")
    classes = ("collapse",)

    def has_add_permission(self, request, obj=None):
        return False


class RegistrationAttachmentInline(TabularInline):
    model = RegistrationAttachment
    extra = 0
    readonly_fields = ("file", "original_name", "description", "uploaded_by", "uploaded_at")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class RegistrationCategoryApprovalInline(TabularInline):
    model = RegistrationCategoryApproval
    extra = 0
    readonly_fields = (
        "category",
        "status",
        "rationale",
        "reviewed_by",
        "reviewed_at",
        "valid_until",
        "version",
        "created_at",
        "updated_at",
    )
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Registration)
class RegistrationAdmin(ModelAdmin):
    list_display = (
        "reference",
        "project_title",
        "company",
        "status",
        "needs_review",
        "created_at",
    )
    list_filter = ("status", "needs_review", "company")
    search_fields = ("project_title", "end_user_name", "company__name")
    readonly_fields = (
        "company",
        "submitted_by",
        "original_submitted_at",
        "version",
        "created_at",
        "updated_at",
    )
    inlines = (
        CompetitorItemInline,
        RegistrationItemInline,
        RegistrationAttachmentInline,
        RegistrationCategoryApprovalInline,
        RegistrationEventInline,
    )

    def save_model(self, request, obj, form, change):
        if change:
            request.registration_prior_snapshot = registration_snapshot(
                self.get_queryset(request).get(pk=obj.pk)
            )
            # Admin edits must invalidate any form or API client holding the old
            # version, otherwise a stale company save overwrites the decision.
            obj.version = obj.version + 1
        else:
            request.registration_prior_snapshot = None
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        if change:
            RegistrationEvent.objects.create(
                registration=form.instance,
                actor=request.user,
                event_type="Admin update",
                details=(
                    "DBGI admin updated registration details or workflow status. "
                    f"Version is now {form.instance.version}."
                ),
                snapshot=request.registration_prior_snapshot or {},
            )
        else:
            RegistrationEvent.objects.create(
                registration=form.instance,
                actor=request.user,
                event_type="Admin created",
                details="Registration created by DBGI admin.",
                snapshot=registration_snapshot(form.instance),
            )


@admin.register(OpportunityRanking)
class OpportunityRankingAdmin(ModelAdmin):
    list_display = (
        "opportunity_title",
        "scope_name",
        "calculated_rank_display",
        "company",
        "registration_link",
        "original_submitted_at",
    )
    list_display_links = None
    list_filter = ("opportunity_scope__opportunity", "opportunity_scope")
    search_fields = (
        "opportunity_scope__opportunity__title",
        "opportunity_scope__name",
        "company__name",
        "project_title",
    )
    ordering = (
        "opportunity_scope__opportunity__title",
        "opportunity_scope__name",
        "original_submitted_at",
        "id",
    )
    actions = None

    def get_queryset(self, request):
        earliest_company_registration = (
            Registration.objects.filter(
                status=Registration.Status.ELIGIBLE_MATCHED,
                opportunity_scope_id=OuterRef("opportunity_scope_id"),
                company_id=OuterRef("company_id"),
            )
            .order_by("original_submitted_at", "id")
            .values("id")[:1]
        )
        return (
            super()
            .get_queryset(request)
            .filter(
                status=Registration.Status.ELIGIBLE_MATCHED,
                opportunity_scope__isnull=False,
                id=Subquery(earliest_company_registration),
            )
            .select_related("company", "opportunity_scope__opportunity")
            .annotate(
                calculated_rank=Window(
                    expression=Rank(),
                    partition_by=[F("opportunity_scope_id")],
                    order_by=F("original_submitted_at").asc(),
                )
            )
        )

    @admin.display(description="Opportunity", ordering="opportunity_scope__opportunity__title")
    def opportunity_title(self, obj):
        return obj.opportunity_scope.opportunity.title

    @admin.display(description="Ranking scope", ordering="opportunity_scope__name")
    def scope_name(self, obj):
        return obj.opportunity_scope.name

    @admin.display(description="Rank", ordering="calculated_rank")
    def calculated_rank_display(self, obj):
        return obj.calculated_rank

    @admin.display(description="Registration")
    def registration_link(self, obj):
        url = reverse("admin:registrations_registration_change", args=(obj.pk,))
        return format_html('<a href="{}">{}</a>', url, obj.reference)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RegistrationEvent)
class RegistrationEventAdmin(ModelAdmin):
    list_display = ("registration", "event_type", "actor", "created_at")
    list_filter = ("event_type", "created_at")
    search_fields = ("registration__project_title", "details")
    readonly_fields = ("registration", "actor", "event_type", "details", "snapshot", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MatchingSuggestion)
class MatchingSuggestionAdmin(ModelAdmin):
    list_display = ("registration", "outcome", "confidence", "score", "rule_version", "created_at")
    list_filter = ("outcome", "confidence", "rule_version", "is_current")
    readonly_fields = (
        "registration",
        "candidate_scope",
        "outcome",
        "confidence",
        "score",
        "supporting_factors",
        "conflicting_factors",
        "rule_version",
        "is_current",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RegistrationReviewDecision)
class RegistrationReviewDecisionAdmin(ModelAdmin):
    list_display = ("registration", "decision", "actor", "created_at")
    list_filter = ("decision", "created_at")
    readonly_fields = (
        "registration",
        "suggestion",
        "opportunity_scope",
        "decision",
        "rationale",
        "actor",
        "registration_version",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class RegistrationItemApprovalInline(TabularInline):
    model = RegistrationItemApproval
    extra = 0


@admin.register(RegistrationCategoryApproval)
class RegistrationCategoryApprovalAdmin(ModelAdmin):
    list_display = (
        "registration",
        "category",
        "status",
        "valid_until",
        "reviewed_by",
        "reviewed_at",
    )
    list_filter = ("status", "category", "valid_until")
    search_fields = ("registration__project_title", "registration__company__name", "category")
    readonly_fields = ("version", "created_at", "updated_at")
    inlines = (RegistrationItemApprovalInline,)

    def save_model(self, request, obj, form, change):
        request.commercial_prior_snapshot = registration_snapshot(obj.registration)
        if change:
            obj.version += 1
        obj.reviewed_by = request.user
        obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        registration = form.instance.registration
        registration.version += 1
        registration.save(update_fields=("version", "updated_at"))
        RegistrationEvent.objects.create(
            registration=registration,
            actor=request.user,
            event_type="Commercial decision",
            details=(
                f"{form.instance.category} pricing was marked "
                f"{form.instance.get_status_display()} through Django administration."
            ),
            snapshot=request.commercial_prior_snapshot,
        )


@admin.register(PriceApprovalRenewal)
class PriceApprovalRenewalAdmin(ModelAdmin):
    list_display = (
        "category_approval",
        "status",
        "requested_by",
        "requested_at",
        "new_valid_until",
        "decided_by",
    )
    list_filter = ("status", "requested_at")
    search_fields = (
        "category_approval__registration__project_title",
        "category_approval__registration__company__name",
    )
    readonly_fields = (
        "category_approval",
        "requested_by",
        "reason",
        "status",
        "previous_valid_until",
        "new_valid_until",
        "decided_by",
        "decision_reason",
        "requested_at",
        "decided_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass
