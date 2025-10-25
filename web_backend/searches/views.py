from rest_framework import viewsets, filters, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import UserSearch, SearchResult
from .serializers import UserSearchSerializer, SearchResultSerializer

class UserSearchViewSet(viewsets.ModelViewSet):
    queryset = UserSearch.objects.select_related("insurance_network").all().order_by("-created_at")
    serializer_class = UserSearchSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["insurance_network", "created_at"]
    search_fields = ["query"]
    ordering_fields = ["created_at", "id"]

    @action(detail=True, methods=["post"])
    def run(self, request, pk=None):
        """
        (Optional stub) Kick off your Nemotron + Tavily pipeline.
        For the hackathon, you can accept payload like:
        { "nemotron_response": {...}, "tavily_results": {...}, "results": [{provider: 1, match_score: 0.9, reason: "…"}, ...] }
        """
        search = self.get_object()
        payload = request.data or {}
        # Save metadata if supplied
        changed = False
        for field in ("nemotron_response", "tavily_results"):
            if field in payload:
                setattr(search, field, payload[field])
                changed = True
        if changed:
            search.save()

        # Bulk create SearchResult if provided
        created = []
        for r in payload.get("results", []):
            sr = SearchResult.objects.create(
                search=search,
                provider_id=r.get("provider"),
                match_score=r.get("match_score", 0.0),
                reason=r.get("reason", "")
            )
            created.append(sr.id)
        return Response({"ok": True, "created_result_ids": created}, status=status.HTTP_200_OK)

class SearchResultViewSet(viewsets.ModelViewSet):
    queryset = SearchResult.objects.select_related("search", "provider").all().order_by("-id")
    serializer_class = SearchResultSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["search", "provider"]
    search_fields = ["reason", "search__query", "provider__name"]
    ordering_fields = ["match_score", "id"]
