from django.contrib import admin
from .models import UserSettings

@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ("user", "age", "insurance_network", "insurance_plan", "default_radius_miles", "updated_at")
    list_filter = ("insurance_network", "insurance_plan")
    search_fields = ("user__username", "user__email")
