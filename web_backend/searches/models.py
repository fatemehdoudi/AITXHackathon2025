from django.db import models
from insurance_networks.models import InsuranceNetwork
from providers.models import Provider

class UserSearch(models.Model):
    query = models.TextField(help_text="User's freeform description of their ailment or concern.")
    insurance_network = models.ForeignKey(InsuranceNetwork, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # You could store metadata from Nemotron or Tavily here:
    nemotron_response = models.JSONField(null=True, blank=True)
    tavily_results = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"Search #{self.id} - {self.query[:50]}..."


class SearchResult(models.Model):
    search = models.ForeignKey(UserSearch, related_name='results', on_delete=models.CASCADE)
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)
    match_score = models.FloatField(default=0.0)
    reason = models.TextField(blank=True, help_text="Explanation or reasoning provided by Nemotron or Tavily.")
    
    def __str__(self):
        return f"Result for Search #{self.search.id}: {self.provider.name}"
