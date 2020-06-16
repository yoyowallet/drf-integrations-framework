from django.contrib.auth.models import AbstractUser
from django.db import models

from drf_integrations.integrations.models import BasePerformedByIntegration


class Organisation(models.Model):
    name = models.TextField()

    def __str__(self):
        return self.name


class User(AbstractUser):
    organisation = models.ForeignKey(Organisation, null=True, on_delete=models.PROTECT)


class IntegrationUser(models.Model):
    integration_name = models.TextField()
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    integration_user_id = models.TextField()

    class Meta:
        unique_together = [("integration_name", "user")]

    def __str__(self):
        return f"{self.user} ({self.integration_name})"


class UserPurchase(BasePerformedByIntegration, models.Model):
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    integration_user = models.ForeignKey(IntegrationUser, on_delete=models.PROTECT, editable=False)
    amount = models.IntegerField(editable=False)
    currency = models.CharField(max_length=3, editable=False)

    def __str__(self):
        return f"{self.integration_user} {self.currency} purchase for {self.amount}"
