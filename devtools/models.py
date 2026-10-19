from registrations.models import Company


class ScenarioLab(Company):
    class Meta:
        proxy = True
        verbose_name = "scenario lab"
        verbose_name_plural = "scenario lab"
