from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from drf_integrations.models import AbstractApplicationInstallation


class PerformedByIntegrationQuerySet(models.QuerySet):
    def performed_by(self, *, installation: "AbstractApplicationInstallation"):
        return self.filter(**installation.get_external_data_source_lookup())
