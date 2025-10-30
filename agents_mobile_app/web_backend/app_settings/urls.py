from rest_framework.routers import DefaultRouter
from .views import UserSettingsViewSet

router = DefaultRouter()
router.register(r"app-settings", UserSettingsViewSet, basename="user-settings")

urlpatterns = router.urls
