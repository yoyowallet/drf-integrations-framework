from rest_framework import status, viewsets
from rest_framework.response import Response

from drf_integrations import integrations

from ..models import IntegrationUser, User


class UserViewSet(viewsets.ViewSet):
    required_alternate_scopes = {
        "POST": [["user:write"]],
        "PUT": [["user:write"]],
    }

    def create(self, request):
        username = request.data["username"]
        email = request.data["email"]
        User.objects.create_user(
            username=username,
            email=email,
            organisation_id=request.auth_context.installation.organisation_id,
        )
        return Response(status=status.HTTP_201_CREATED)

    def update(self, request, pk):
        user = User.objects.get(
            pk=pk,
            organisation_id=request.auth_context.installation.organisation_id,
        )

        IntegrationUser.objects.bulk_create(
            IntegrationUser(
                user=user,
                integration_name=integrations.get(integration_name).name,
                integration_user_id=user_id,
            )
            for integration_name, user_id in request.data["integration_user_ids"]
        )

        return Response(status=status.HTTP_201_CREATED)
