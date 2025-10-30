from django.contrib import admin
from .models import UserSearch, SearchResult

class SearchResultInline(admin.TabularInline):
    model = SearchResult
    extra = 0
    autocomplete_fields = ("provider",)
    fields = ("provider", "match_score", "reason")
    readonly_fields = ()
    show_change_link = True

@admin.register(UserSearch)
class UserSearchAdmin(admin.ModelAdmin):
    list_display = ("id", "short_query", "insurance_network", "created_at")
    list_filter = ("insurance_network", "created_at")
    search_fields = ("query",)
    date_hierarchy = "created_at"
    inlines = [SearchResultInline]
    readonly_fields = ("created_at",)
    fieldsets = (
        (None, {"fields": ("query", "insurance_network")}),
        ("Agent Metadata", {"fields": ("nemotron_response", "tavily_results")}),
        ("Timestamps", {"fields": ("created_at",)}),
    )

    def short_query(self, obj):
        return (obj.query[:60] + "…") if len(obj.query) > 60 else obj.query
    short_query.short_description = "Query"

@admin.register(SearchResult)
class SearchResultAdmin(admin.ModelAdmin):
    list_display = ("search", "provider", "match_score")
    list_filter = ("provider__provider_type",)
    search_fields = (
        "search__query",
        "provider__name",
        "reason",
    )
    autocomplete_fields = ("search", "provider")
