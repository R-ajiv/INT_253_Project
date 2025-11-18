from __future__ import annotations

import os
import tempfile
from typing import IO
import shutil
from django.conf import settings


class AudioTranscriptionError(Exception):
    pass


def _whisper_available() -> bool:
    try:
        import whisper
        return True
    except Exception:
        return False


def transcribe_audio_file(django_file) -> str:
    if not settings.CALL_INPUT_FORMAT.get('accepts_audio', False):
        raise AudioTranscriptionError('Audio input is disabled by configuration.')

    if not _whisper_available():
        raise AudioTranscriptionError(
            'Audio transcription requires optional dependency "openai-whisper". '
            'Install with: pip install openai-whisper'
        )

    suffix = os.path.splitext(getattr(django_file, 'name', 'audio'))[1] or '.wav'
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        for chunk in django_file.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        import whisper

        # Allow an explicit ffmpeg executable path via settings.FFMPEG_PATH.
        # This helps when the Django process has a different PATH than your
        # interactive shell (common for services, containers, or IDE run configs).
        ffmpeg_path = getattr(settings, 'FFMPEG_PATH', None)
        original_path = None
        if ffmpeg_path:
            # Accept either a directory or full path to the executable.
            if os.path.isdir(ffmpeg_path):
                ffmpeg_dir = ffmpeg_path
                ffmpeg_exe = os.path.join(ffmpeg_dir, 'ffmpeg.exe' if os.name == 'nt' else 'ffmpeg')
            else:
                ffmpeg_exe = ffmpeg_path
                ffmpeg_dir = os.path.dirname(ffmpeg_exe) or ffmpeg_exe

            if not os.path.exists(ffmpeg_exe):
                raise AudioTranscriptionError(
                    f'Configured FFMPEG_PATH does not exist: {ffmpeg_exe}'
                )

            # Prepend ffmpeg directory to PATH for the duration of the transcribe call
            original_path = os.environ.get('PATH', '')
            os.environ['PATH'] = ffmpeg_dir + os.pathsep + original_path
        else:
            # No explicit path configured — check PATH for ffmpeg
            if shutil.which('ffmpeg') is None:
                raise AudioTranscriptionError(
                    'ffmpeg not found. Whisper requires the ffmpeg binary to be installed '
                    'and available on PATH. You can either add ffmpeg to your PATH (e.g. '
                    'add C:\\ffmpeg\\bin to PATH on Windows), or set the absolute path '
                    'in Django settings as FFMPEG_PATH = r"C:\\ffmpeg\\bin\\ffmpeg.exe". '
                    'If you installed ffmpeg while the server was running, restart the process.'
                )

        # Run transcription while ensuring we restore PATH afterwards if we modified it
        try:
            model = whisper.load_model('base')
            result = model.transcribe(tmp_path)
            text = result.get('text', '').strip()
            if not text:
                raise AudioTranscriptionError('Could not transcribe audio or empty result.')
            return text
        finally:
            # Restore original PATH if we modified it
            if original_path is not None:
                os.environ['PATH'] = original_path
    except AudioTranscriptionError:
        raise
    except Exception as exc:
        raise AudioTranscriptionError(f'Audio transcription failed: {exc}')
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


