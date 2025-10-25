from rest_framework.routers import DefaultRouter
from .views import SpecialtyViewSet, ProviderViewSet

router = DefaultRouter()
router.register(r"specialties", SpecialtyViewSet, basename="specialty")
router.register(r"providers", ProviderViewSet, basename="provider")

urlpatterns = router.urls
