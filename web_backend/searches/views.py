# views.py
import re, inspect
from typing import TypedDict, Optional, List, Dict, Any

from asgiref.sync import sync_to_async, async_to_sync
from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from langgraph.graph import StateGraph, START, END
from agents.models import get_nemotron
from agents.insurance_network_search import find_portal as _find_portal

from .models import UserSearch, SearchResult
from .serializers import UserSearchSerializer, SearchResultSerializer

# ---------- Graph typing ----------
class GraphState(TypedDict, total=False):
    insurance: Optional[str]
    insurance_id: Optional[str]
    prefix: Optional[str]
    postal_code: Optional[str]
    portal_links: Optional[List[Dict[str, str]]]
    nemotron_summary: Optional[str]

# ---------- LLM + helpers ----------
_llm = get_nemotron()

async def _call_llm(prompt: str):
    if hasattr(_llm, "ainvoke"):
        return await _llm.ainvoke(prompt)
    return await sync_to_async(_llm.invoke)(prompt)

async def _get_user_input(state: GraphState) -> GraphState:
    state.setdefault("insurance", "Blue Cross Blue Shield")
    state.setdefault("insurance_id", "ZGP123456789")
    state.setdefault("postal_code", "77840")
    m = re.match(r"([A-Za-z]{3})", state.get("insurance_id") or "")
    state["prefix"] = m.group(1).upper() if m else None
    return state

if inspect.iscoroutinefunction(_find_portal):
    _find_portal_async = _find_portal
else:
    async def _find_portal_async(state: GraphState) -> GraphState:
        return await sync_to_async(_find_portal)(state)

async def _summarize_portal(state: GraphState) -> GraphState:
    portals = state.get("portal_links") or []
    if not portals:
        state["nemotron_summary"] = "No portal links found."
        return state
    links_text = "\n".join(f"{p['title']} - {p['url']}" for p in portals)
    prompt = (
        f"Given these links for {state['insurance']}, identify the most reliable portal "
        f"for finding in-network providers. Reply concisely with reasoning.\n{links_text}"
    )
    msg = await _call_llm(prompt)
    state["nemotron_summary"] = getattr(msg, "content", str(msg))
    return state

# ---------- Build graph once ----------
_graph = StateGraph(GraphState)
_graph.add_node("GetUserInput", _get_user_input)
_graph.add_node("FindPortal", _find_portal_async)
_graph.add_node("SummarizePortal", _summarize_portal)
_graph.add_edge(START, "GetUserInput")
_graph.add_edge("GetUserInput", "FindPortal")
_graph.add_edge("FindPortal", "SummarizePortal")
_graph.add_edge("SummarizePortal", END)
app_graph = _graph.compile()

# ---------- ViewSets ----------
class UserSearchViewSet(viewsets.ModelViewSet):
    queryset = UserSearch.objects.select_related("insurance_network").all().order_by("-created_at")
    serializer_class = UserSearchSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["insurance_network", "created_at"]
    search_fields = ["query"]
    ordering_fields = ["created_at", "id"]

    # IMPORTANT: keep this sync. Do not mark it async.
    def create(self, request, *args, **kwargs):
        return async_to_sync(self._create_async)(request, *args, **kwargs)

    # Your async logic lives here
    async def _create_async(self, request, *args, **kwargs):
        payload: Dict[str, Any] = request.data or {}

        # 1) Create the row (ORM is sync → wrap)
        search: UserSearch = await sync_to_async(UserSearch.objects.create)(
            query=payload.get("query", ""),
            insurance_network_id=payload.get("insurance_network"),
        )

        # 2) Run the LangGraph with request inputs
        init_state: GraphState = {
            "insurance": payload.get("insurance"),
            "insurance_id": payload.get("insurance_id"),
            "postal_code": payload.get("postal_code"),
        }
        state: GraphState = await app_graph.ainvoke(init_state)

        # 3) Persist any outputs
        changed = False
        if state.get("nemotron_summary") is not None:
            search.nemotron_response = state["nemotron_summary"]
            changed = True
        if changed:
            await sync_to_async(search.save)()

        # 4) Serialize & return a real Response (not a coroutine)
        data = await sync_to_async(lambda: UserSearchSerializer(search).data)()
        data["graph_state"] = state
        return Response(data, status=status.HTTP_201_CREATED)


class SearchResultViewSet(viewsets.ModelViewSet):
    queryset = SearchResult.objects.select_related("search", "provider").all().order_by("-id")
    serializer_class = SearchResultSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["search", "provider"]
    search_fields = ["reason", "search__query", "provider__name"]
    ordering_fields = ["match_score", "id"]
