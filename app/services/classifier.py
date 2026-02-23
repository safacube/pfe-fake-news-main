import os
from functools import lru_cache
from typing import Dict
from transformers import pipeline

DEFAULT_MODEL = 'mrm8488/bert-tiny-finetuned-fake-news-detection'
LABEL_MAP = {
    'FAKE': 'Fake',
    'REAL': 'Real',
    'LABEL_0': 'Real',
    'LABEL_1': 'Fake',
}


@lru_cache(maxsize=1)
def _load_model():
    model_name = os.getenv('HUGGINGFACE_MODEL', DEFAULT_MODEL)
    return pipeline('text-classification', model=model_name)


def classify_text(text: str) -> Dict[str, str]:
    cleaned = ' '.join((text or '').split())
    if not cleaned:
        return {'label': 'Unknown', 'score': 0.0}

    # Trim aggressively to avoid exceeding model position embeddings (e.g., 512 tokens for BERT).
    snippet = ' '.join(cleaned.split()[:400])

    try:
        classifier = _load_model()
        tokenizer = getattr(classifier, 'tokenizer', None)
        model_max = getattr(tokenizer, 'model_max_length', 512) or 512
        safe_max = min(model_max, 512)  # keep within typical BERT limits to avoid overflow
        prediction = classifier(snippet, truncation=True, max_length=safe_max)[0]
        raw_label = prediction.get('label', 'Unknown')
        label = LABEL_MAP.get(raw_label, raw_label)
        score = float(prediction.get('score', 0.0))
        return {'label': label, 'score': round(score, 4)}
    except Exception as exc:  # noqa: BLE001
        return {'label': 'Error', 'score': 0.0, 'error': str(exc)}
