from rest_framework.routers import DefaultRouter
from .views import InsurancePlanViewSet

router = DefaultRouter()
router.register(r"insurance-plans", InsurancePlanViewSet, basename="insurance-plan")

urlpatterns = router.urls
