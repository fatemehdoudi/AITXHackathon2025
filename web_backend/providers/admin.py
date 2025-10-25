from django.contrib import admin
from .models import Provider, Specialty

@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name",)
    ordering = ("name",)

@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = (
        "name", "provider_type", "specialty",
        "city", "state", "zip_code",
        "accepts_new_patients",
    )
    list_filter = (
        "provider_type",
        "specialty",
        "accepts_new_patients",
        "insurance_networks",
        "state",
    )
    search_fields = (
        "name", "city", "state", "zip_code",
        "phone", "website",
    )
    filter_horizontal = ("insurance_networks",)  # easier M2M selection
    list_editable = ("accepts_new_patients",)
    readonly_fields = ("latitude", "longitude")
    fieldsets = (
        ("Basic Info", {
            "fields": ("name", "provider_type", "specialty", "accepts_new_patients")
        }),
        ("Contact & Location", {
            "fields": ("address", "city", "state", "zip_code", "phone", "website")
        }),
        ("Networks", {
            "fields": ("insurance_networks",)
        }),
        ("Geo (optional)", {
            "fields": ("latitude", "longitude"),
            "classes": ("collapse",)
        }),
    )
    list_per_page = 25
