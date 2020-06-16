from rest_framework import routers

from . import ecommerce_viewsets

router = routers.DefaultRouter()

router.register(
    r"ecommerce/purchase", ecommerce_viewsets.PurchasesViewSet, basename="api-purchases"
)

urlpatterns = router.urls
