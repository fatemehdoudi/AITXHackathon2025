from rest_framework import viewsets, permissions, decorators, response, status
from .models import UserSettings
from .serializers import UserSettingsSerializer

class UserSettingsViewSet(viewsets.ModelViewSet):
    """
    Minimal CRUD.
    Includes a handy /app-settings/me/ endpoint to get or create the current user's settings.
    """
    queryset = UserSettings.objects.select_related("user", "insurance_network", "insurance_plan").all().order_by("id")
    serializer_class = UserSettingsSerializer
    permission_classes = [permissions.AllowAny]  # swap to IsAuthenticated when you add auth

    @decorators.action(detail=False, methods=["get", "patch", "post"], url_path="me")
    def me(self, request):
        """
        GET  /app-settings/me/      -> fetch current user's settings (creates if missing when authenticated)
        PATCH /app-settings/me/     -> update current user's settings
        POST /app-settings/me/      -> create if not exists (useful without auth by passing user id)
        """
        # If you have auth, prefer request.user.id; otherwise allow ?user=<id> for hackathon
        user_id = getattr(request.user, "id", None) or request.query_params.get("user") or request.data.get("user")
        if not user_id:
            return response.Response({"detail": "Provide user id (auth or ?user=)."}, status=400)

        obj, _created = UserSettings.objects.get_or_create(user_id=user_id)
        if request.method in ["PATCH", "POST"]:
            ser = self.get_serializer(obj, data=request.data, partial=True)
            ser.is_valid(raise_exception=True)
            ser.save()
            return response.Response(ser.data, status=status.HTTP_200_OK)
        return response.Response(self.get_serializer(obj).data)
