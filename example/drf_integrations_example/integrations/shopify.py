import hmac
import logging
from hashlib import sha256
from typing import TYPE_CHECKING, Dict, List, Optional

from django import forms
from django.contrib.auth.models import AnonymousUser
from oauth2_provider.contrib.rest_framework import TokenHasScope
from oauth2_provider.models import get_access_token_model, get_application_model
from rest_framework import routers, status, viewsets
from rest_framework.authentication import BaseAuthentication
from rest_framework.response import Response

from drf_integrations.integrations.base import BaseIntegration, BaseIntegrationForm
from drf_integrations.models import get_application_installation_model

if TYPE_CHECKING:
    from rest_framework.request import Request

logger = logging.getLogger(__name__)


Application = get_application_model()
ApplicationInstallation = get_application_installation_model()
AccessToken = get_access_token_model()


class ShopifyConfigForm(BaseIntegrationForm):
    shopify_shop = forms.CharField()
    shared_secret = forms.CharField()

    def set_initial_values(
        self, *, target, integration, application=None, **kwargs,
    ):
        if application:
            if application.internal_integration_name != ShopifyIntegration.name:
                raise ValueError(
                    f"Cannot use {self.__class__.__name__} with "
                    f"integration {application.internal_integration_name}"
                )
        else:
            application = Application.objects.get_by_internal_integration(ShopifyIntegration)

        super().set_initial_values(
            target=target, integration=integration, application=application, **kwargs,
        )

    @classmethod
    def clean_form_data(cls, installation_form: "forms.Form") -> Dict:
        data = super().clean_form_data(installation_form)

        shopify_shop = data["shopify_shop"]
        organisation_id = data.get("organisation_id")
        if organisation_id and (
            ApplicationInstallation.objects.filter(config__shopify_shop=shopify_shop)
            .exclude(client_id=organisation_id)
            .exists()
        ):
            raise forms.ValidationError(
                {
                    "shopify_shop": {
                        f"There is already an existing installation with shop {shopify_shop}"
                    }
                }
            )

        return data


class ShopifyIntegration(BaseIntegration):
    name = "shopify"
    display_name = "Shopify"
    config_form_class = ShopifyConfigForm
    default_scopes = ["purchase:shopify:write", "webhook:shopify:write"]

    def get_urls(self) -> List:
        router = routers.DefaultRouter()
        router.register("webhook", ShopifyWebhookViewSet, basename="shopify")
        return router.urls

    @classmethod
    def get_installation_lookup_from_request(cls, request: "Request", **kwargs) -> Dict:
        return cls.get_installation_lookup_from_config_values(
            shopify_shop=(
                request.headers.get("X-Shopify-Hmac-Sha256") or request.query_params.get("shop")
            )
        )


class ShopifyBaseAuthBackend(BaseAuthentication):
    def _validate_required(self, request) -> bool:
        raise NotImplementedError()

    def _get_signature(self, request) -> Optional[bool]:
        raise NotImplementedError()

    def _get_signature_values(self, request) -> Optional[bool]:
        raise NotImplementedError()

    def authenticate(self, request):
        if not self._validate_required(request):
            logger.info("integrations.shopify.missing_params")
            return None

        try:
            installation = ApplicationInstallation.objects.select_related("application").get(
                **ShopifyIntegration.get_installation_lookup_from_request(
                    request=request, application=None
                )
            )
        except (
            ApplicationInstallation.DoesNotExist,
            ApplicationInstallation.MultipleObjectsReturned,
        ):
            logger.info("integrations.shopify.application_setup_not_found")
            return None

        context = installation.get_context()
        signature = self._get_signature(request)
        signature_values = self._get_signature_values(request)

        if not signature or not signature_values:
            logger.info(
                "integrations.shopify.missing_signature_values",
                extra=dict(signature=signature, signature_values=signature_values),
            )
            return None

        new_signature = hmac.new(
            context.installation.get_config()["shared_secret"].encode(), signature_values, sha256,
        )
        if not hmac.compare_digest(signature.encode("utf-8"), new_signature.encode("utf-8")):
            logger.info(
                "integrations.shopify.invalid_signature",
                extra=dict(
                    request=request,
                    headers=request.headers,
                    queryparams=request.query_params,
                    signature=signature,
                    calculated_signature=new_signature,
                ),
            )
            return None

        request.auth_context = context

        return (
            AnonymousUser(),
            AccessToken.objects.create_for_internal_integration(
                application=installation.application
            ),
        )


class ShopifyProxyBackend(ShopifyBaseAuthBackend):
    required_queryparams = (
        "shop",
        "signature",
    )

    def _validate_required(self, request) -> bool:
        return all(request.query_params.get(key) for key in self.required_queryparams)

    def _get_signature(self, request):
        queryparams = {
            key: ",".join(sorted(values))
            for key, values in request.query_params.lists()
            if key != "signature"
        }
        encoded_params = "&".join(
            (f"{key}={queryparams[key]}" for key in sorted(queryparams.keys()))
        )
        return encoded_params

    def _get_signature_values(self, request):
        return request.query_params["signature"]


class ShopifyWebhookBackend(ShopifyBaseAuthBackend):
    required_headers = (
        "X-Shopify-Hmac-Sha256",
        "X-Shopify-Shop-Domain",
    )

    def _validate_required(self, request) -> bool:
        return all(key in request.headers for key in self.required_headers)

    def _get_signature(self, request):
        return request.headers["X-Shopify-Hmac-Sha256"]

    def _get_signature_values(self, request):
        return request.body


class ShopifyPermission(TokenHasScope):
    def has_permission(self, request, view):
        return isinstance(
            request.successful_authenticator, ShopifyBaseAuthBackend
        ) and super().has_permission(request, view)


class ShopifyWebhookViewSet(viewsets.ViewSet):
    authentication_classes = (ShopifyWebhookBackend,)
    permission_classes = (ShopifyPermission,)
    required_scopes = ("webhook:shopify:write",)

    def create(self, request):
        logger.info(
            "integrations.shopify.webhook",
            extra=dict(data=request.data, installation=request.auth_context.installation),
        )

        return Response(status=status.HTTP_200_OK)
