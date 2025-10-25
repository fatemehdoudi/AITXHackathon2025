from django.contrib import admin
from .models import InsurancePlan

@admin.register(InsurancePlan)
class InsurancePlanAdmin(admin.ModelAdmin):
    list_display = ("name", "network", "plan_type")
    list_filter = ("network", "plan_type")
    search_fields = ("name", "network__name", "plan_code")
