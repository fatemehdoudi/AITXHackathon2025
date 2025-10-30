from django.db import models
from insurance_networks.models import InsuranceNetwork

class InsurancePlan(models.Model):
    PLAN_TYPES = [
        ('HMO', 'HMO'),
        ('PPO', 'PPO'),
        ('EPO', 'EPO'),
        ('POS', 'POS'),
        ('OTHER', 'Other'),
    ]

    network = models.ForeignKey(InsuranceNetwork, on_delete=models.CASCADE, related_name="plans")
    name = models.CharField(max_length=150)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, blank=True)
    plan_code = models.CharField(max_length=50, blank=True, help_text="Optional internal or government code.")
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.network.name} – {self.name}"

    class Meta:
        unique_together = [("network", "name")]