from typing import TYPE_CHECKING

from django.db import models

from drf_integrations.integrations import managers

if TYPE_CHECKING:
    from drf_integrations.models import AbstractApplicationInstallation


class BasePerformedByIntegration(models.Model):
    class Meta:
        abstract = True

    performed_by_installation_id = models.PositiveIntegerField(
        null=True, default=None, db_index=True, editable=False
    )

    objects = managers.PerformedByIntegrationQuerySet.as_manager()

    def set_performed_by(self, *, installation: "AbstractApplicationInstallation"):
        self.performed_by_installation_id = installation.pk
