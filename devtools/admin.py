from django.conf import settings
from django.contrib import admin, messages
from django.db import transaction
from django.http import Http404
from django.template.response import TemplateResponse
from unfold.admin import ModelAdmin

from .models import ScenarioLab
from .scenarios import SCENARIOS, clear_transactional_records, load_scenario


@admin.register(ScenarioLab)
class ScenarioLabAdmin(ModelAdmin):
    change_list_template = "admin/devtools/scenario_lab.html"

    def has_module_permission(self, request):
        return settings.DEBUG and request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return settings.DEBUG and request.user.is_superuser

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        if not settings.DEBUG or not request.user.is_superuser:
            raise Http404

        result = None
        cleared = None
        selected = request.POST.get("scenario", "automatic_exact")
        clear_requested = request.POST.get("clear_transactional") == "on"
        if request.method == "POST":
            if selected not in SCENARIOS:
                messages.error(request, "Choose a valid development scenario.")
            elif clear_requested and request.POST.get("confirmation", "").strip() != (
                "CLEAR TRANSACTIONS"
            ):
                messages.error(
                    request,
                    "Type CLEAR TRANSACTIONS exactly before clearing transactional records.",
                )
            else:
                with transaction.atomic():
                    if clear_requested:
                        cleared = clear_transactional_records()
                    result = load_scenario(selected, request.user)
                messages.success(request, f"Loaded scenario: {SCENARIOS[selected].title}.")

        context = {
            **self.admin_site.each_context(request),
            "title": "Scenario Lab",
            "subtitle": "Load safe, documented development workflows",
            "opts": self.model._meta,
            "scenarios": SCENARIOS.values(),
            "selected": selected,
            "clear_requested": clear_requested,
            "result": result,
            "cleared": cleared,
            **(extra_context or {}),
        }
        request.current_app = self.admin_site.name
        return TemplateResponse(request, self.change_list_template, context)
