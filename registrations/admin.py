from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .audit import registration_snapshot
from .models import (
    Company,
    CompetitorItem,
    Product,
    Registration,
    RegistrationAttachment,
    RegistrationEvent,
    RegistrationItem,
    User,
)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "partner_code", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "partner_code")


@admin.register(User)
class PortalUserAdmin(UserAdmin):
    fieldsets = (*UserAdmin.fieldsets, ("Portal access", {"fields": ("company", "role")}))
    add_fieldsets = (
        *UserAdmin.add_fieldsets,
        (
            "Portal access",
            {"fields": ("company", "role", "is_staff", "is_superuser", "is_active")},
        ),
    )
    list_display = ("username", "email", "company", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active", "company")
    search_fields = ("username", "email", "company__name")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "category", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("code", "name", "category")


class CompetitorItemInline(admin.TabularInline):
    model = CompetitorItem
    extra = 0


class RegistrationItemInline(admin.TabularInline):
    model = RegistrationItem
    extra = 0


class RegistrationEventInline(admin.TabularInline):
    model = RegistrationEvent
    extra = 0
    can_delete = False
    readonly_fields = ("actor", "event_type", "details", "snapshot", "created_at")

    def has_add_permission(self, request, obj=None):
        return False


class RegistrationAttachmentInline(admin.TabularInline):
    model = RegistrationAttachment
    extra = 0
    readonly_fields = ("file", "original_name", "description", "uploaded_by", "uploaded_at")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
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
    readonly_fields = ("company", "submitted_by", "created_at", "updated_at")
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
class RegistrationEventAdmin(admin.ModelAdmin):
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
