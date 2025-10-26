from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="app_settings")

    # basics
    age = models.PositiveIntegerField(null=True, blank=True)

    # insurance (optional)
    insurance_network = models.ForeignKey(
        "insurance_networks.InsuranceNetwork",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="user_settings"
    )
    insurance_plan = models.ForeignKey(
        "insurance_plans.InsurancePlan",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="user_settings"
    )

    group_id = models.CharField(max_length=100, null=True, blank=True)
    member_id = models.CharField(max_length=100, null=True, blank=True)

    # search
    default_radius_miles = models.PositiveIntegerField(default=25)

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Settings for user {self.user_id}"
