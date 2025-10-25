from rest_framework.routers import DefaultRouter
from .views import InsuranceNetworkViewSet

router = DefaultRouter()
router.register(r"insurance-networks", InsuranceNetworkViewSet, basename="insurance-network")

urlpatterns = router.urls
