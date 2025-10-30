from rest_framework import serializers
from .models import UserSearch, SearchResult

class SearchResultSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source="provider.name", read_only=True)

    class Meta:
        model = SearchResult
        fields = ["id", "search", "provider", "provider_name", "match_score", "reason"]

class UserSearchSerializer(serializers.ModelSerializer):
    # Include results read-only by default; you can POST to /search-results/ to add
    results = SearchResultSerializer(many=True, read_only=True)

    class Meta:
        model = UserSearch
        fields = [
            "id", "query", "insurance_network", "created_at",
            "nemotron_response", "tavily_results", "results",
        ]
        read_only_fields = ["created_at"]
