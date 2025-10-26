from django.contrib import admin
from .models import Prospect, ContactLog

@admin.register(Prospect)
class ProspectAdmin(admin.ModelAdmin):
    list_display = ("user", "status", "next_action_at", "last_contacted_at", "updated_at")
    list_filter = ("status",)
    search_fields = ("notes", "initial_reason")

@admin.register(ContactLog)
class ContactLogAdmin(admin.ModelAdmin):
    list_display = ("prospect", "method", "outcome", "contacted_at")
    list_filter = ("method",)
    search_fields = ("outcome", "notes")
