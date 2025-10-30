from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Prospect, ContactLog
from .serializers import ProspectSerializer, ContactLogSerializer

class ProspectViewSet(viewsets.ModelViewSet):
    queryset = (
        Prospect.objects
        .select_related("user", "search")
        .all()
        .order_by("-updated_at")
    )
    serializer_class = ProspectSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["user", "status", "search"]
    search_fields = ["initial_reason", "notes"]
    ordering_fields = ["updated_at", "created_at", "next_action_at"]

    @action(detail=False, methods=["post"], url_path="toggle")
    def toggle(self, request):
        """
        POST /outreach/prospects/toggle/
        Body: {"user":1,"provider":42, "search":7, "initial_reason":"good ortho", "match_score_snapshot":0.91}
        Creates if not exists; if exists and status=Saved -> deletes; else sets to Saved.
        """
        user = request.data.get("user")
        if not user:
            return Response({"detail":"user is required."}, status=400)
        
        provider_payload = request.data.get("provider") or {}

        obj, created = Prospect.objects.get_or_create(
            user_id=user,
            defaults={
                "status": Prospect.Status.SAVED,
                "search_id": request.data.get("search"),
                "initial_reason": request.data.get("initial_reason", ""),
                "match_score_snapshot": request.data.get("match_score_snapshot"),
                "provider_data": provider_payload,
            },
        )
        if not created:
            # simple favorite toggle: if already SAVED, remove; else set SAVED
            if obj.status == Prospect.Status.SAVED and not request.data.get("force_keep", False):
                obj.delete()
                return Response({"toggled": "removed"}, status=200)
            obj.status = Prospect.Status.SAVED
            obj.save()
        return Response(ProspectSerializer(obj).data, status=201 if created else 200)

    @action(detail=True, methods=["post"], url_path="log-contact")
    def log_contact(self, request, pk=None):
        """
        POST /outreach/prospects/{id}/log-contact/
        Body: {"method":"PHONE","outcome":"Left voicemail","notes":"Called main line"}
        Also bumps status to CONTACTED and sets last_contacted_at=now.
        """
        prospect = self.get_object()
        ser = ContactLogSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        contact = ser.save(prospect=prospect)

        # update prospect quick facts
        from django.utils import timezone
        prospect.status = Prospect.Status.CONTACTED
        prospect.last_contacted_at = timezone.now()
        prospect.save(update_fields=["status", "last_contacted_at"])

        return Response(ContactLogSerializer(contact).data, status=status.HTTP_201_CREATED)

class ContactLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ContactLog.objects.select_related("prospect").all().order_by("-contacted_at")
    serializer_class = ContactLogSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["prospect", "method"]
    search_fields = ["notes", "outcome"]
    ordering_fields = ["contacted_at", "id"]
