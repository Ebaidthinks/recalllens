"""
Generate improvement suggestions based on analysis results
"""

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def make_suggestions(
    recall_score: float,
    text_tokens: List[Dict[str, Any]],
    salience_data: Dict[str, Any],
    env_params: Dict[str, Any]
) -> List[Dict[str, str]]:
    """
    Generate actionable suggestions to improve ad recall.

    Args:
        recall_score: Overall recall score (0-100)
        text_tokens: OCR text tokens with legibility data
        salience_data: Visual salience analysis
        env_params: Environmental parameters

    Returns:
        List of suggestions with category, priority, description, and impact
    """
    logger.info("Generating improvement suggestions")

    suggestions = []

    # Text Legibility Suggestions
    if text_tokens:
        illegible_count = sum(1 for t in text_tokens if not t['legible'])
        legibility_rate = 1 - (illegible_count / len(text_tokens))

        if legibility_rate < 0.5:
            suggestions.append({
                'category': 'Text Legibility',
                'priority': 'high',
                'description': 'Over 50% of text is illegible. Increase font size by at least 40% and use bold, high-contrast fonts.',
                'impact_estimate': '+15-25 points to recall score'
            })
        elif legibility_rate < 0.75:
            suggestions.append({
                'category': 'Text Legibility',
                'priority': 'medium',
                'description': 'Some text is hard to read. Increase font size by 20-30% and improve contrast.',
                'impact_estimate': '+8-15 points to recall score'
            })

        # Check for too much text
        if len(text_tokens) > 5:
            suggestions.append({
                'category': 'Message Simplicity',
                'priority': 'high',
                'description': f'Too many text elements ({len(text_tokens)} detected). Reduce to 3-5 key words for better recall at high speeds.',
                'impact_estimate': '+10-20 points to recall score'
            })
    else:
        suggestions.append({
            'category': 'Content',
            'priority': 'high',
            'description': 'No text detected. Add clear, large text to communicate your message.',
            'impact_estimate': '+20-30 points to recall score'
        })

    # Visual Salience Suggestions
    attention_score = salience_data.get('attention_score', 0)
    if attention_score < 30:
        suggestions.append({
            'category': 'Visual Impact',
            'priority': 'high',
            'description': 'Low visual salience detected. Use brighter colors, stronger contrast, or bold imagery to grab attention.',
            'impact_estimate': '+15-20 points to recall score'
        })
    elif attention_score < 50:
        suggestions.append({
            'category': 'Visual Impact',
            'priority': 'medium',
            'description': 'Moderate visual interest. Consider adding a focal point or increasing color contrast.',
            'impact_estimate': '+8-12 points to recall score'
        })

    # Speed-Specific Suggestions
    speed_kmh = env_params['speed_kmh']
    if speed_kmh > 100:
        suggestions.append({
            'category': 'High-Speed Optimization',
            'priority': 'high',
            'description': 'Ad will be viewed at high speed (>100 km/h). Use extra-large fonts (minimum 30cm letter height) and limit text to 5 words or less.',
            'impact_estimate': '+12-18 points to recall score'
        })

    # Lighting Suggestions
    if env_params['lighting'] in ['dusk', 'night']:
        suggestions.append({
            'category': 'Lighting',
            'priority': 'medium',
            'description': f'Poor visibility in {env_params["lighting"]} conditions. Consider adding illumination or using reflective materials.',
            'impact_estimate': '+8-15 points to recall score'
        })

    # Distraction Suggestions
    if env_params['phone_distraction'] in ['med', 'high']:
        suggestions.append({
            'category': 'Distraction Mitigation',
            'priority': 'medium',
            'description': 'High distraction environment. Use extremely simple messaging (3 words max) and very bold, attention-grabbing visuals.',
            'impact_estimate': '+10-15 points to recall score'
        })

    # Overall Score Suggestions
    if recall_score < 40:
        suggestions.append({
            'category': 'Overall Design',
            'priority': 'critical',
            'description': 'Very low recall score (<40). Complete redesign recommended: simplify message to 3 words, increase font size 50%+, use high-contrast colors.',
            'impact_estimate': '+30-40 points to recall score'
        })
    elif recall_score < 60:
        suggestions.append({
            'category': 'Overall Design',
            'priority': 'high',
            'description': 'Below-average recall score. Simplify message, increase text size, and strengthen visual hierarchy.',
            'impact_estimate': '+15-25 points to recall score'
        })

    # Sort by priority
    priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    suggestions.sort(key=lambda x: priority_order.get(x['priority'], 3))

    logger.info(f"Generated {len(suggestions)} suggestions")
    return suggestions
