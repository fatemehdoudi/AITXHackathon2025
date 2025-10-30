from django.contrib import admin
from .models import InsuranceNetwork

@admin.register(InsuranceNetwork)
class InsuranceNetworkAdmin(admin.ModelAdmin):
    list_display = ("name", "website", "phone_number")
    search_fields = ("name",)
    list_per_page = 25
