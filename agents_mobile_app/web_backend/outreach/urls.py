from rest_framework.routers import DefaultRouter
from .views import ProspectViewSet, ContactLogViewSet

router = DefaultRouter()
router.register(r"outreach/prospects", ProspectViewSet, basename="prospect")
router.register(r"outreach/contacts", ContactLogViewSet, basename="contactlog")

urlpatterns = router.urls
