"""
Memory recall computation based on cognitive science principles
"""

from typing import Dict, Any, List
import numpy as np
import logging

logger = logging.getLogger(__name__)


def compute_recall(
    text_tokens: List[Dict[str, Any]],
    salience_data: Dict[str, Any],
    env_params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compute predicted memory recall score based on multiple factors.

    Memory recall is influenced by:
    - Text legibility (can the driver read it?)
    - Visual salience (does it grab attention?)
    - Environmental conditions (speed, lighting, distractions)
    - Cognitive load factors

    Args:
        text_tokens: List of OCR text tokens with legibility data
        salience_data: Visual salience analysis results
        env_params: Environmental parameters

    Returns:
        Dictionary with recall score, predicted gist, and retention factors
    """
    logger.info("Computing recall score")

    # Initialize factors
    factors = {}

    # Factor 1: Text Legibility (0-30 points)
    if text_tokens:
        legible_count = sum(1 for t in text_tokens if t['legible'])
        legibility_rate = legible_count / len(text_tokens)
        avg_confidence = sum(t['confidence'] for t in text_tokens) / len(text_tokens)
        factors['legibility'] = legibility_rate * avg_confidence * 30
    else:
        factors['legibility'] = 0.0

    # Factor 2: Visual Salience (0-25 points)
    attention_score = salience_data.get('attention_score', 0)
    factors['salience'] = (attention_score / 100) * 25

    # Factor 3: Speed Impact (0-20 points)
    # Lower speed = better recall
    speed_kmh = env_params['speed_kmh']
    speed_penalty = (140 - speed_kmh) / 80  # Normalize to 0-1
    factors['speed'] = speed_penalty * 20

    # Factor 4: Dwell Time (0-15 points)
    # Longer dwell = better recall
    dwell_sec = env_params['dwell_sec']
    dwell_bonus = (dwell_sec - 0.5) / 1.5  # Normalize to 0-1
    factors['dwell_time'] = dwell_bonus * 15

    # Factor 5: Lighting Conditions (0-5 points)
    lighting_map = {'day': 5, 'dusk': 3, 'night': 1}
    factors['lighting'] = lighting_map.get(env_params['lighting'], 3)

    # Factor 6: Phone Distraction Penalty (0-5 points)
    distraction_map = {'low': 5, 'med': 3, 'high': 0}
    factors['distraction'] = distraction_map.get(env_params['phone_distraction'], 3)

    # Calculate total recall score (0-100)
    recall_score = sum(factors.values())
    recall_score = max(0, min(100, recall_score))  # Clamp to 0-100

    # Generate predicted gist (what the driver will remember)
    predicted_gist = _generate_gist(text_tokens, recall_score, salience_data)

    logger.info(f"Recall score: {recall_score:.2f}")

    return {
        'recall_score': float(recall_score),
        'predicted_gist': predicted_gist,
        'retention_factors': {k: float(v) for k, v in factors.items()}
    }


def _generate_gist(
    text_tokens: List[Dict[str, Any]],
    recall_score: float,
    salience_data: Dict[str, Any]
) -> str:
    """
    Generate a predicted gist of what the driver will remember.

    Args:
        text_tokens: OCR text tokens
        recall_score: Overall recall score
        salience_data: Salience analysis data

    Returns:
        Predicted gist string
    """
    if not text_tokens:
        return "No text detected - driver may only recall colors and shapes"

    # Get legible text only
    legible_texts = [t['text'] for t in text_tokens if t['legible']]

    if not legible_texts:
        return "Text present but illegible - driver unlikely to recall specific message"

    # Sort by confidence and take top texts
    sorted_tokens = sorted(
        [t for t in text_tokens if t['legible']],
        key=lambda x: x['confidence'],
        reverse=True
    )

    # Number of words recalled depends on recall score
    if recall_score >= 75:
        num_words = min(len(legible_texts), 5)
        confidence = "high"
    elif recall_score >= 50:
        num_words = min(len(legible_texts), 3)
        confidence = "moderate"
    elif recall_score >= 25:
        num_words = min(len(legible_texts), 2)
        confidence = "low"
    else:
        num_words = 1
        confidence = "very low"

    top_texts = [t['text'] for t in sorted_tokens[:num_words]]
    gist = " ".join(top_texts)

    return f"{gist} ({confidence} confidence)"
