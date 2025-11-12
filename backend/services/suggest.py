"""
Generate improvement suggestions based on analysis results
"""
from typing import Dict, List


def make_suggestions(
    recall_data: Dict,
    text_data: Dict,
    salience_data: Dict,
    speed_kmh: float,
    dwell_sec: float
) -> List[Dict]:
    """
    Generate actionable suggestions to improve ad recall

    Args:
        recall_data: Memory analysis from compute_recall()
        text_data: OCR results from extract_text_tokens()
        salience_data: Attention data from analyze_salience()
        speed_kmh: Vehicle speed
        dwell_sec: Dwell time

    Returns:
        List of suggestions, each with:
        - category: Type of issue (text/color/layout/contrast)
        - severity: Impact level (low/medium/high)
        - issue: Description of the problem
        - fix: Recommended action
        - impact: Expected improvement
    """
    suggestions = []

    recall_score = recall_data.get("recall_score", 0.0)
    legibility_score = text_data.get("legibility_score", 0.0)
    attention_score = salience_data.get("attention_score", 0.0)
    cognitive_load = recall_data.get("cognitive_load", 0.0)
    token_count = len(text_data.get("tokens", []))

    # Text legibility issues
    if legibility_score < 0.5:
        suggestions.append({
            "category": "text",
            "severity": "high",
            "issue": f"Low text legibility ({legibility_score:.2f}/1.0) at {speed_kmh} km/h",
            "fix": "Increase font size by 2-3x and use bold, sans-serif fonts",
            "impact": "Could improve recall by 30-40%"
        })

    if legibility_score < 0.7 and speed_kmh > 100:
        suggestions.append({
            "category": "text",
            "severity": "medium",
            "issue": f"Text may blur at high speed ({speed_kmh} km/h)",
            "fix": "Use thicker font weights and increase letter spacing",
            "impact": "Could improve recall by 15-20%"
        })

    # Token count and cognitive load
    if token_count > 7:
        suggestions.append({
            "category": "layout",
            "severity": "high",
            "issue": f"Too much text ({token_count} words) for {dwell_sec}s viewing time",
            "fix": "Reduce to 3-5 key words maximum. Use hierarchy: one main message",
            "impact": "Could improve recall by 40-50%"
        })
    elif token_count > 5:
        suggestions.append({
            "category": "layout",
            "severity": "medium",
            "issue": f"{token_count} words may be too many for quick comprehension",
            "fix": "Consider reducing to 3-4 most important words",
            "impact": "Could improve recall by 20-25%"
        })

    # Attention issues
    if attention_score < 0.4:
        suggestions.append({
            "category": "color",
            "severity": "high",
            "issue": f"Low visual attention capture ({attention_score:.2f}/1.0)",
            "fix": "Use high-contrast colors (e.g., yellow/black, white/blue) and larger visual elements",
            "impact": "Could improve recall by 35-45%"
        })

    focus_regions = salience_data.get("focus_regions", [])
    if len(focus_regions) > 3:
        suggestions.append({
            "category": "layout",
            "severity": "medium",
            "issue": f"Too many focal points ({len(focus_regions)}) competing for attention",
            "fix": "Simplify design to 1-2 main visual elements",
            "impact": "Could improve recall by 25-30%"
        })

    # Cognitive load
    if cognitive_load > 0.7:
        suggestions.append({
            "category": "layout",
            "severity": "high",
            "issue": f"High cognitive load ({cognitive_load:.2f}/1.0) makes processing difficult",
            "fix": "Simplify message, increase text size, reduce visual clutter",
            "impact": "Could improve recall by 30-40%"
        })

    # Recall-specific suggestions
    if recall_score < 0.3:
        suggestions.append({
            "category": "contrast",
            "severity": "high",
            "issue": f"Very low recall probability ({recall_score:.2f}/1.0)",
            "fix": "Complete redesign needed: larger text, fewer words, higher contrast",
            "impact": "Could improve recall by 50-70%"
        })
    elif recall_score < 0.5:
        suggestions.append({
            "category": "contrast",
            "severity": "medium",
            "issue": f"Below-average recall probability ({recall_score:.2f}/1.0)",
            "fix": "Boost contrast, simplify message, and increase key element sizes",
            "impact": "Could improve recall by 30-40%"
        })

    # If everything is good
    if not suggestions:
        suggestions.append({
            "category": "layout",
            "severity": "low",
            "issue": "Design performs well overall",
            "fix": "Minor refinements: Consider A/B testing color variations",
            "impact": "Could improve recall by 5-10%"
        })

    return suggestions
