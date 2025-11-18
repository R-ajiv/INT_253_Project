from typing import Any
from django.conf import settings
from rest_framework import serializers
from .utils.validators import validate_audio_extension


class TextSentimentRequestSerializer(serializers.Serializer):
    transcript = serializers.CharField(allow_blank=False, max_length=20000)


class AudioSentimentRequestSerializer(serializers.Serializer):
    audio_file = serializers.FileField()

    def validate_audio_file(self, value: Any):
        validate_audio_extension(value)
        max_mb = settings.CALL_INPUT_FORMAT.get('max_file_mb', 25)
        if value.size and value.size > max_mb * 1024 * 1024:
            raise serializers.ValidationError(f"File too large. Max {max_mb} MB allowed.")
        return value


