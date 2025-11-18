from __future__ import annotations

from typing import Dict, List, Any, Tuple
from functools import lru_cache
from django.conf import settings
from transformers import pipeline  # type: ignore


FINAL_LABELS = ('positive', 'negative', 'mixed', 'neutral')
CONFIDENCE_WEAK = 0.55


class SentimentService:
    @staticmethod
    @lru_cache(maxsize=1)
    def _get_pipeline():
        model_name: str = settings.SENTIMENT_MODEL.get('name')
        device: str = settings.SENTIMENT_MODEL.get('device', 'cpu')
        return pipeline(
            task='sentiment-analysis',
            model=model_name,
            device=-1 if device == 'cpu' else 0,
        )

    @staticmethod
    def _harmonize_label(raw_label: str) -> str:
        label = raw_label.upper()
        if 'POS' in label:
            return 'positive'
        if 'NEG' in label:
            return 'negative'
        return label.lower()

    @staticmethod
    def _categorize_segment(raw_label: str, score: float) -> Tuple[str, float]:
        base = SentimentService._harmonize_label(raw_label)
        if score < CONFIDENCE_WEAK:
            return 'neutral', score
        return base, score

    @staticmethod
    def _aggregate_labels(segment_labels: List[str], scores: List[float]) -> Dict[str, Any]:
        counts: Dict[str, int] = {label: segment_labels.count(label) for label in FINAL_LABELS}
        total = sum(counts.values()) or 1

        if counts['positive'] and counts['negative']:
            summary_label = 'mixed'
        elif counts['positive']:
            summary_label = 'positive'
        elif counts['negative']:
            summary_label = 'negative'
        else:
            summary_label = 'neutral'

        avg_confidence = sum(scores) / max(len(scores), 1)
        distribution = {label: counts[label] / total for label in FINAL_LABELS if counts[label]}

        return {
            'label': summary_label,
            'confidence': round(avg_confidence, 4),
            'distribution': distribution,
        }

    @staticmethod
    def predict_text(text: str) -> Dict[str, Any]:
        pl = SentimentService._get_pipeline()
        output_type: str = settings.SENTIMENT_OUTPUT_TYPE
        batch_size: int = int(settings.SENTIMENT_MODEL.get('batch_size', 8))

        segments: List[str]
        if len(text) > 512:
            segments = [s.strip() for s in text.replace('\n', ' ').split('.') if s.strip()]
        else:
            segments = [text]

        raw_results = pl(segments, batch_size=batch_size, truncation=True)
        harmonized_segments = []
        segment_labels: List[str] = []
        scores: List[float] = []

        for idx, result in enumerate(raw_results):
            score = float(result['score'])
            label, _ = SentimentService._categorize_segment(result['label'], score)
            segment_labels.append(label)
            scores.append(score)
            harmonized_segments.append({
                'segment': segments[idx],
                'raw_label': result['label'],
                'label': label,
                'score': score,
            })

        summary = SentimentService._aggregate_labels(segment_labels, scores)

        if output_type == 'label':
            return {'label': summary['label']}

        if output_type == 'label_score':
            return {
                'label': summary['label'],
                'confidence': summary['confidence'],
            }

        return {
            'summary': summary,
            'segments': harmonized_segments,
        }


