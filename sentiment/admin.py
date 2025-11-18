from django.contrib import admin

from .models import SentimentAnalysisResult


@admin.register(SentimentAnalysisResult)
class SentimentAnalysisResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'summary_label', 'summary_confidence', 'source', 'created_at')
    list_filter = ('summary_label', 'source', 'created_at')
    search_fields = ('user__username', 'transcript_preview')
