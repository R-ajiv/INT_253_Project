from django.conf import settings
import os
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import TextSentimentRequestSerializer, AudioSentimentRequestSerializer
from .ml.service import SentimentService
from .preprocessing.cleaning import preprocess_text_for_sentiment
from .utils.audio import transcribe_audio_file, AudioTranscriptionError
from .models import SentimentAnalysisResult

from django.db.models import Count
import json


def _extract_label(results):
    summary = results.get('summary') if isinstance(results, dict) else None
    if summary:
        return summary.get('label', 'neutral').lower()
    return results.get('label', 'neutral').lower()


def _extract_confidence(results):
    summary = results.get('summary') if isinstance(results, dict) else None
    if summary:
        return float(summary.get('confidence') or summary.get('average_score') or 0.0)
    return float(results.get('confidence') or results.get('score') or 0.0)


def _extract_distribution(results):
    summary = results.get('summary') if isinstance(results, dict) else None
    if summary:
        return summary.get('distribution') or {}
    return {}


def _extract_segments(results):
    return results.get('segments') if isinstance(results, dict) else []


class AuthenticatedAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]


import shutil


class HealthcheckView(AuthenticatedAPIView):
    def get(self, request: HttpRequest) -> Response:
        # Report basic app health and whether ffmpeg is available to this process.
        ffmpeg_ok = False
        ffmpeg_info = None
        ffmpeg_path = getattr(settings, 'FFMPEG_PATH', None)
        if ffmpeg_path:
            # If explicit path configured, validate it.
            ffmpeg_info = ffmpeg_path
            if os.path.isdir(ffmpeg_path):
                candidate = os.path.join(ffmpeg_path, 'ffmpeg.exe' if os.name == 'nt' else 'ffmpeg')
            else:
                candidate = ffmpeg_path
            ffmpeg_ok = os.path.exists(candidate)
        else:
            which = shutil.which('ffmpeg')
            ffmpeg_ok = which is not None
            ffmpeg_info = which

        return Response({
            'status': 'ok',
            'model': settings.SENTIMENT_MODEL.get('name'),
            'output_type': settings.SENTIMENT_OUTPUT_TYPE,
            'ffmpeg_available': ffmpeg_ok,
            'ffmpeg_path': ffmpeg_info,
        })


class AnalyzeTextView(AuthenticatedAPIView):
    def post(self, request: HttpRequest) -> Response:
        serializer = TextSentimentRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        text = serializer.validated_data['transcript']
        cleaned_text = preprocess_text_for_sentiment(text)
        results = SentimentService.predict_text(cleaned_text)
        saved = SentimentAnalysisResult.objects.create(
            user=request.user,
            source=SentimentAnalysisResult.Source.TRANSCRIPT,
            summary_label=_extract_label(results),
            summary_confidence=_extract_confidence(results),
            distribution=_extract_distribution(results),
            segments=_extract_segments(results),
            transcript_preview=cleaned_text[:500],
        )
        return Response({'analysis': results, 'result_id': saved.id}, status=status.HTTP_200_OK)


class AnalyzeAudioView(AuthenticatedAPIView):
    def post(self, request: HttpRequest) -> Response:
        serializer = AudioSentimentRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        audio_file = serializer.validated_data['audio_file']
        try:
            transcript = transcribe_audio_file(audio_file)
        except AudioTranscriptionError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        cleaned_text = preprocess_text_for_sentiment(transcript)
        results = SentimentService.predict_text(cleaned_text)
        saved = SentimentAnalysisResult.objects.create(
            user=request.user,
            source=SentimentAnalysisResult.Source.AUDIO,
            summary_label=_extract_label(results),
            summary_confidence=_extract_confidence(results),
            distribution=_extract_distribution(results),
            segments=_extract_segments(results),
            transcript_preview=cleaned_text[:500],
        )
        return Response({'transcript': transcript, 'analysis': results, 'result_id': saved.id}, status=status.HTTP_200_OK)


class SentimentResultDeleteView(AuthenticatedAPIView):
    def delete(self, request: HttpRequest, pk: int) -> Response:
        try:
            result = SentimentAnalysisResult.objects.get(pk=pk, user=request.user)
        except SentimentAnalysisResult.DoesNotExist:
            return Response({'detail': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        result.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@login_required
def ui_home(request: HttpRequest) -> HttpResponse:
    results_qs = SentimentAnalysisResult.objects.filter(user=request.user)
    counts = {
        row['summary_label']: row['count'] for row in results_qs.values('summary_label').annotate(count=Count('id'))
    }
    total = sum(counts.values())
    history = [
        {
            'id': result.id,
            'label': result.summary_label,
            'confidence': result.summary_confidence,
            'distribution': result.distribution,
            'segments': result.segments,
            'source': result.get_source_display(),
            'transcript_preview': result.transcript_preview,
            'created_at': result.created_at.isoformat(),
        }
        for result in results_qs[:10]
    ]

    context = {
        'model_name': settings.SENTIMENT_MODEL.get('name'),
        'output_type': settings.SENTIMENT_OUTPUT_TYPE,
        'call_input': settings.CALL_INPUT_FORMAT,
        'initial_payload': json.dumps({
            'total': total,
            'counts': counts,
            'history': history,
        }),
    }
    return render(request, 'sentiment/index.html', context)
