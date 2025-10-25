from rest_framework.routers import DefaultRouter
from .views import UserSearchViewSet, SearchResultViewSet

router = DefaultRouter()
router.register(r"searches", UserSearchViewSet, basename="user-search")
router.register(r"search-results", SearchResultViewSet, basename="search-result")

urlpatterns = router.urls
