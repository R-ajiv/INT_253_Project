# Helpdesk Sentiment Analysis (Django Prototype)

A Django-based prototype for analyzing helpdesk call sentiment using HuggingFace Transformers. Supports text transcripts and optional audio transcription (via Whisper).

## Requirements
- Python 3.12+ (works with 3.13 tested)
- Windows/macOS/Linux

## Quickstart

```bash
python -m venv .venv
# Windows PowerShell
\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser  # create dashboard credentials
python manage.py runserver
```

Sign in via `http://127.0.0.1:8000/accounts/login/` (use the credentials you just created), then access the dashboard at `http://127.0.0.1:8000/`. The interface focuses on the transcript/audio analyzers, live sentiment counters, and a recent-results timeline (persisted per user) in a clean neutral theme.

## API Endpoints
- POST `/api/sentiment/analyze/text/` JSON: `{ "transcript": "..." }`
- POST `/api/sentiment/analyze/audio/` multipart: `audio_file=<file>` (requires `openai-whisper` optional)
- GET `/api/sentiment/health/`

Responses map sentiments to four categories: **positive**, **negative**, **neutral**, and **mixed** (when positive/negative signals appear together). Detailed mode returns per-segment breakdown plus distribution and confidence.

## Configuration
Edit `helpdesk_sentiment/settings.py` or create `helpdesk_sentiment/local_settings.py` to override:

- `SENTIMENT_MODEL`:
  - `name`: default `distilbert-base-uncased-finetuned-sst-2-english`
  - `device`: `cpu` or `cuda`
  - `batch_size`: integer
- `CALL_INPUT_FORMAT`:
  - `accepts_text`: bool
  - `accepts_audio`: bool
  - `max_file_mb`: int
  - `allowed_audio_extensions`: list
- `SENTIMENT_OUTPUT_TYPE`: `label`, `label_score`, or `detailed`

## Audio Transcription (Optional)
Install Whisper for audio support:

```bash
pip install openai-whisper
```

Large models may require FFmpeg. See Whisper docs.

## Screenshots
<img width="417" height="390" alt="image" src="https://github.com/user-attachments/assets/d1a484bd-a803-4e92-bac1-c7e86aa6e9cc" />
<img width="899" height="864" alt="image" src="https://github.com/user-attachments/assets/a73912f2-a251-4bf4-92e7-c3042498a0ea" />
<img width="873" height="662" alt="image" src="https://github.com/user-attachments/assets/ab6ef0e4-612b-4c28-91f0-1c86a0aae681" />


## Notes on ML
- This prototype uses a general sentiment classifier; for helpdesk domain adaptation, fine-tune on labeled support-call data.
- Consider bias evaluation and calibration across customer demographics.
- Track metrics (accuracy, F1) via an evaluation script before production.

## Example curl

```bash
curl -X POST http://127.0.0.1:8000/api/sentiment/analyze/text/ \
  -H "Content-Type: application/json" \
  -d '{"transcript":"I waited 30 minutes. The agent was helpful though."}'
```

## License
MIT


