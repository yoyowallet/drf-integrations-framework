from datetime import timedelta

import factory
from django.utils import timezone

from drf_integrations import models


class ApplicationFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Application


class ApplicationInstallationFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.ApplicationInstallation

    application = factory.SubFactory(ApplicationFactory)


class AccessTokenFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.AccessToken

    expires = timezone.now() + timedelta(days=1)
