import os
from django.conf import settings
from rest_framework import serializers


def validate_audio_extension(uploaded_file) -> None:
    allowed = settings.CALL_INPUT_FORMAT.get('allowed_audio_extensions', [])
    ext = os.path.splitext(getattr(uploaded_file, 'name', ''))[1].lower()
    if allowed and ext not in allowed:
        raise serializers.ValidationError(f"Unsupported file type: {ext}. Allowed: {', '.join(allowed)}")


