"""
Memory and recall scoring based on cognitive load
"""
import numpy as np
from typing import Dict, List


def compute_recall(
    text_data: Dict,
    salience_data: Dict,
    speed_kmh: float,
    dwell_sec: float,
    phone_distraction: str
) -> Dict:
    """
    Compute recall likelihood and predict what viewers remember

    Args:
        text_data: OCR results from extract_text_tokens()
        salience_data: Attention data from analyze_salience()
        speed_kmh: Vehicle speed
        dwell_sec: Dwell time
        phone_distraction: Distraction level

    Returns:
        Dictionary with:
        - recall_score: Overall recall probability (0-1)
        - predicted_gist: What viewers likely remember
        - token_recall: Per-token recall probabilities
        - cognitive_load: Processing difficulty score (0-1)
    """
    # Base recall starts from legibility and attention
    legibility = text_data.get("legibility_score", 0.0)
    attention = salience_data.get("attention_score", 0.0)

    # Speed penalty: faster = harder to process
    speed_factor = max(0, 1.0 - ((speed_kmh - 60) / 120))  # 60 kmh = 1.0, 140 kmh = 0.33

    # Dwell time bonus: longer = better encoding
    dwell_factor = min(dwell_sec / 2.0, 1.0)  # 2 seconds = optimal

    # Distraction penalty
    distraction_factor = {
        "low": 1.0,
        "med": 0.6,
        "high": 0.3
    }.get(phone_distraction, 1.0)

    # Cognitive load: how hard is it to process?
    # Higher load = lower recall
    text_complexity = len(text_data.get("tokens", [])) / 10.0  # More text = higher load
    speed_load = (speed_kmh - 60) / 80.0  # Faster = higher load
    distraction_load = 1.0 - distraction_factor

    cognitive_load = min(
        (text_complexity * 0.4 + speed_load * 0.3 + distraction_load * 0.3),
        1.0
    )

    # Final recall score
    recall_score = (
        legibility * 0.3 +
        attention * 0.3 +
        speed_factor * 0.15 +
        dwell_factor * 0.15 +
        distraction_factor * 0.1
    )
    recall_score = max(0.0, min(recall_score, 1.0))

    # Per-token recall based on position and attention overlap
    tokens = text_data.get("tokens", [])
    positions = text_data.get("positions", [])
    confidences = text_data.get("confidences", [])
    focus_regions = salience_data.get("focus_regions", [])

    token_recall = []
    for i, (token, pos, conf) in enumerate(zip(tokens, positions, confidences)):
        # Base token recall from OCR confidence
        base_recall = conf * recall_score

        # Bonus if token is in a focus region
        in_focus = False
        if focus_regions:
            token_center_x = (pos[0] + pos[2]) / 2
            token_center_y = (pos[1] + pos[3]) / 2

            for region in focus_regions:
                if (region[0] <= token_center_x <= region[2] and
                    region[1] <= token_center_y <= region[3]):
                    in_focus = True
                    break

        if in_focus:
            base_recall *= 1.3  # 30% boost for focused text

        token_recall.append({
            "token": token,
            "recall_probability": min(base_recall, 1.0)
        })

    # Predict gist: what will viewers remember?
    # Select top tokens by recall probability
    if token_recall:
        sorted_tokens = sorted(token_recall, key=lambda x: x["recall_probability"], reverse=True)
        top_tokens = [t["token"] for t in sorted_tokens[:5]]  # Top 5 tokens
        predicted_gist = " ".join(top_tokens)
    else:
        predicted_gist = "[Nothing memorable]"

    return {
        "recall_score": recall_score,
        "predicted_gist": predicted_gist,
        "token_recall": token_recall,
        "cognitive_load": cognitive_load
    }
