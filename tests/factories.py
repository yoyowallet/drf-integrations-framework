import factory
from datetime import timedelta
from django.utils import timezone

from drf_integrations import models


class ApplicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Application


class ApplicationInstallationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ApplicationInstallation

    application = factory.SubFactory(ApplicationFactory)


class AccessTokenFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.AccessToken

    expires = timezone.now() + timedelta(days=1)
