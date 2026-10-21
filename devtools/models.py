from django.conf import settings
from django.db import models

from registrations.models import Company


class ScenarioLab(Company):
    class Meta:
        proxy = True
        verbose_name = "scenario lab"
        verbose_name_plural = "scenario lab"


class RegistrationTestPreset(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="registration_test_presets",
    )
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=240, blank=True)
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "id"]  # noqa: RUF012 - Django Meta convention
        constraints = [  # noqa: RUF012 - Django Meta convention
            models.UniqueConstraint(
                fields=["owner", "name"],
                name="unique_registration_test_preset_name_per_user",
            )
        ]

    def __str__(self):
        return self.name
