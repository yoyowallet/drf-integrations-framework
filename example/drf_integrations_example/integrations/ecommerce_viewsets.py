from rest_framework import status, viewsets
from rest_framework.response import Response

from example.drf_integrations_example import models
from example.drf_integrations_example.integrations.shopify import (
    ShopifyPermission,
    ShopifyProxyBackend,
)


class PurchasesViewSet(viewsets.ViewSet):
    authentication_classes = (ShopifyProxyBackend,)
    permission_classes = (ShopifyPermission,)
    required_scopes = ("purchase:shopify:write",)

    def create(self, request):
        user_id = request.data["user_id"]
        integration = request.auth_context.installation.application.get_integration_instance()
        try:
            integration_user = models.IntegrationUser.objects.get(
                integration_name=integration.name,
                integration_user_id=user_id,
                user__organisation_id=request.auth_context.installation.organisation_id,
            )
        except models.IntegrationUser.DoesNotExist:
            return Response(
                data=dict(error=f"User {user_id} does not exist"),
                status=status.HTTP_400_BAD_REQUEST,
            )

        purchase = models.UserPurchase(
            integration_user=integration_user,
            amount=request.data["amount"],
            currency=request.data["currency"],
        )
        purchase.set_performed_by(installation=request.auth_context.installation)
        purchase.save()

        return Response(status=status.HTTP_201_CREATED)
