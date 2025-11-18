from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class SentimentAnalysisResult(models.Model):
    class Source(models.TextChoices):
        TRANSCRIPT = 'transcript', _('Transcript')
        AUDIO = 'audio', _('Audio')

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sentiment_results')
    source = models.CharField(max_length=16, choices=Source.choices)
    summary_label = models.CharField(max_length=16)
    summary_confidence = models.FloatField(default=0.0)
    distribution = models.JSONField(default=dict, blank=True)
    segments = models.JSONField(default=list, blank=True)
    transcript_preview = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.summary_label} ({self.source})"
from django.db import models

# Create your models here.
