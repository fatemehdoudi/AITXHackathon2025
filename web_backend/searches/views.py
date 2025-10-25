# views.py
import inspect
from typing import TypedDict, Optional, List, Dict, Any

from asgiref.sync import sync_to_async, async_to_sync
from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

# ⬇️ NEW: use the compiled graph from agents/main.py
from agents.main import app as agent_app

from .models import UserSearch, SearchResult
from .serializers import UserSearchSerializer, SearchResultSerializer


# ---------- Graph typing (aligned to agents/main.py) ----------
class GraphState(TypedDict, total=False):
    insurance: Optional[str]
    specialty: Optional[str]
    location: Optional[str]
    postal_code: Optional[str]
    providers: Optional[List[Dict[str, Any]]]


# ---------- ViewSets ----------
class UserSearchViewSet(viewsets.ModelViewSet):
    queryset = UserSearch.objects.select_related("insurance_network").all().order_by("-created_at")
    serializer_class = UserSearchSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["insurance_network", "created_at"]
    search_fields = ["query"]
    ordering_fields = ["created_at", "id"]

    # Keep this sync to satisfy DRF; bridge to async with async_to_sync
    def create(self, request, *args, **kwargs):
        return async_to_sync(self._create_async)(request, *args, **kwargs)

    # Your async work happens here
    async def _create_async(self, request, *args, **kwargs):
        payload: Dict[str, Any] = request.data or {}

        # 1) Create the row (ORM is sync → wrap in sync_to_async)
        search: UserSearch = await sync_to_async(UserSearch.objects.create)(
            query=payload.get("query", ""),
            insurance_network_id=payload.get("insurance_network"),
        )

        # 2) Prepare state for the new agents/main.py graph
        #    (falls back to the same defaults your main.py currently uses)
        init_state: GraphState = {
            "insurance": payload.get("insurance") or "Blue Cross Blue Shield",
            "specialty": payload.get("specialty") or "Cardiology",
            "location": payload.get("location") or "College Station, TX 77840",
            "postal_code": payload.get("postal_code") or "77840",
        }

        # 3) Run the LangGraph
        state: GraphState = await agent_app.ainvoke(init_state)

        # 4) Optionally persist anything you'd like from `state`
        #    (Keeping this minimal/neutral since model fields vary project-to-project)
        #    Example: store a summary count in a generic text field if you have one.
        #    If you already have a JSONField (e.g., `search.graph_state`), you can save it.
        changed = False
        providers = state.get("providers") or []
        if hasattr(search, "providers_count"):
            search.providers_count = len(providers)
            changed = True
        if hasattr(search, "graph_state"):
            # If you have a JSONField on your model
            search.graph_state = state  # type: ignore[attr-defined]
            changed = True
        if changed:
            await sync_to_async(search.save)()

        # 5) Serialize & return a real Response (not a coroutine)
        data = await sync_to_async(lambda: UserSearchSerializer(search).data)()
        data["graph_state"] = state  # expose the providers, etc., to the client
        return Response(data, status=status.HTTP_201_CREATED)


class SearchResultViewSet(viewsets.ModelViewSet):
    queryset = SearchResult.objects.select_related("search", "provider").all().order_by("-id")
    serializer_class = SearchResultSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["search", "provider"]
    search_fields = ["reason", "search__query", "provider__name"]
    ordering_fields = ["match_score", "id"]
