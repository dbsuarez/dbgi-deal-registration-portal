from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from unfold.admin import ModelAdmin, TabularInline
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .audit import registration_snapshot
from .models import (
    Company,
    CompetitorItem,
    MatchingSuggestion,
    Opportunity,
    OpportunityScope,
    Product,
    Registration,
    RegistrationAttachment,
    RegistrationEvent,
    RegistrationItem,
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
    list_display = ("code", "name", "category", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("code", "name", "category")


class OpportunityScopeInline(TabularInline):
    model = OpportunityScope
    extra = 0


@admin.register(Opportunity)
class OpportunityAdmin(ModelAdmin):
    list_display = ("title", "end_user_name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("title", "end_user_name", "end_user_address")
    readonly_fields = ("created_by", "created_at")
    inlines = (OpportunityScopeInline,)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


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

    def has_add_permission(self, request, obj=None):
        return False


class RegistrationAttachmentInline(TabularInline):
    model = RegistrationAttachment
    extra = 0
    readonly_fields = ("file", "original_name", "description", "uploaded_by", "uploaded_at")
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
        "created_at",
        "updated_at",
    )
    inlines = (
        CompetitorItemInline,
        RegistrationItemInline,
        RegistrationAttachmentInline,
        RegistrationEventInline,
    )

    def save_model(self, request, obj, form, change):
        request.registration_prior_snapshot = (
            registration_snapshot(self.get_queryset(request).get(pk=obj.pk)) if change else None
        )
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        if change:
            RegistrationEvent.objects.create(
                registration=form.instance,
                actor=request.user,
                event_type="Admin update",
                details="DBGI admin updated registration details or workflow status.",
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


admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass
