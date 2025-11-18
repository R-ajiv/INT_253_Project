from django.urls import path
from .views import HealthcheckView, AnalyzeTextView, AnalyzeAudioView, SentimentResultDeleteView

urlpatterns = [
    path('health/', HealthcheckView.as_view(), name='sentiment-health'),
    path('analyze/text/', AnalyzeTextView.as_view(), name='sentiment-analyze-text'),
    path('analyze/audio/', AnalyzeAudioView.as_view(), name='sentiment-analyze-audio'),
    path('results/<int:pk>/', SentimentResultDeleteView.as_view(), name='sentiment-result-detail'),
]


