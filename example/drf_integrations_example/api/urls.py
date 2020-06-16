from rest_framework import routers

from . import viewsets

router = routers.DefaultRouter()

router.register(r"user", viewsets.UserViewSet, basename="api-users")

urlpatterns = router.urls
