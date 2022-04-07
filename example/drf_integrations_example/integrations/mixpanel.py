import logging
from django import forms
from django.db.models import signals
from mixpanel import Mixpanel
from oauth2_provider.models import get_access_token_model, get_application_model

from drf_integrations.integrations.base import BaseClient, BaseIntegration, BaseIntegrationForm
from drf_integrations.models import get_application_installation_model

from ..models import IntegrationUser, User, UserPurchase

logger = logging.getLogger(__name__)

Application = get_application_model()
ApplicationInstallation = get_application_installation_model()
AccessToken = get_access_token_model()


class MixpanelConfigForm(BaseIntegrationForm):
    mixpanel_token = forms.CharField()

    def set_initial_values(
        self,
        *,
        target,
        integration,
        application=None,
        **kwargs,
    ):
        if application:
            if application.internal_integration_name != MixpanelIntegration.name:
                raise ValueError(
                    f"Cannot use {self.__class__.__name__} with "
                    f"integration {application.internal_integration_name}"
                )
        else:
            application = Application.objects.get_by_internal_integration(MixpanelIntegration)

        super().set_initial_values(
            target=target,
            integration=integration,
            application=application,
            **kwargs,
        )


class MixpanelClient(BaseClient):
    def __init__(self, token, **kwargs):
        super().__init__(**kwargs)
        self._client = Mixpanel(token=token)

    def register_purchase(self, user: User, amount: int, currency: str, source_integration: str):
        self._client.track(
            str(user.pk),
            "new_purchase",
            dict(amount=amount, currency=currency, source_integration=source_integration),
        )


class MixpanelIntegration(BaseIntegration):
    name = "mixpanel"
    display_name = "Mixpanel"
    config_form_class = MixpanelConfigForm
    client_class = MixpanelClient


def on_purchase_saved(sender, instance: UserPurchase, **kwargs):
    integration_user = IntegrationUser.objects.select_related("user").get(
        pk=instance.integration_user.pk
    )
    installation = ApplicationInstallation.objects.get(
        organisation_id=integration_user.user.organisation_id,
        **MixpanelIntegration.get_installation_lookup_from_config_values(),
    )
    integration = installation.application.get_integration_instance()
    client: MixpanelClient = integration.get_client(installation.get_context())
    client.register_purchase(
        user=integration_user.user,
        amount=instance.amount,
        currency=instance.currency,
        source_integration=integration_user.integration_name,
    )


signals.post_save.connect(on_purchase_saved, sender=UserPurchase, weak=False)
