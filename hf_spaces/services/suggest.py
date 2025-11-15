"""
Generate actionable recommendations based on recall analysis

Rule-based expert system that provides specific, implementable fixes
to improve billboard recall probability.
"""

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def make_suggestions(
    recall_dict: Dict[str, Any],
    ocr_result: Dict[str, Any],
    sal_result: Dict[str, Any]
) -> List[Dict[str, str]]:
    """
    Generate prioritized, actionable suggestions to improve billboard recall.

    Uses rule-based expert system to identify specific problems and provide
    concrete fixes with estimated impact on recall score.

    Args:
        recall_dict: Memory recall results with score and components
        ocr_result: OCR results with words_detected, logo_visible, etc.
        sal_result: Salience results with hotspot_regions, attention_score, etc.

    Returns:
        List of 3-5 prioritized suggestions, each with:
            - type: "layout", "copy", "contrast"
            - message: specific actionable fix
            - estimated_impact: "Will improve recall by ~X%"
    """
    logger.info("Generating rule-based suggestions")

    suggestions = []

    # Extract key metrics
    words_detected = ocr_result.get('words_detected', [])
    word_count = len(words_detected)
    legible_words = [w for w in words_detected if w.get('legible', False)]

    # Extract component scores from recall calculation
    components = recall_dict.get('_components', {})
    max_word_legibility = components.get('max_word_legibility', 0.0)
    top_region_salience = components.get('top_region_salience', 0.0)

    # =========================================================================
    # RULE 1: Copy Density - Too Many Words
    # =========================================================================
    if word_count > 5:
        # Calculate how much to reduce
        excess_words = word_count - 5

        suggestions.append({
            'type': 'copy',
            'message': f'Reduce copy to ≤5 words; keep only numeral and category. Current: {word_count} words. Remove {excess_words} word(s). Focus on: [NUMBER] + [BENEFIT].',
            'estimated_impact': f'Will improve recall by ~{min(25, excess_words * 3)}%'
        })
        logger.info(f"Rule 1 triggered: {word_count} words > 5 threshold")

    # =========================================================================
    # RULE 2: No Legible Words
    # =========================================================================
    if not legible_words:
        suggestions.append({
            'type': 'contrast',
            'message': 'Increase text size by 150-200% or improve contrast. No legible text detected at highway speeds. Minimum text height should be 22 pixels at simulated viewing distance.',
            'estimated_impact': 'Will improve recall by ~35%'
        })
        logger.info("Rule 2 triggered: No legible words detected")

    # =========================================================================
    # RULE 3: Low Word Legibility (MaxWordLegibility < 0.7)
    # =========================================================================
    elif max_word_legibility < 0.7:
        # Calculate required size increase
        legibility_deficit = 0.7 - max_word_legibility
        size_increase_pct = int(legibility_deficit * 100)  # Rough heuristic

        # Find average height of legible words
        if legible_words:
            avg_height = sum(w.get('height_px', 0) for w in legible_words) / len(legible_words)
            target_height = avg_height * (1 + size_increase_pct / 100)

            suggestions.append({
                'type': 'contrast',
                'message': f'Increase headline size by {size_increase_pct}% to reach minimum legible height. Current avg: {avg_height:.0f}px → Target: {target_height:.0f}px. Use bold fonts and high-contrast color combinations.',
                'estimated_impact': f'Will improve recall by ~{min(20, size_increase_pct // 2)}%'
            })
        else:
            suggestions.append({
                'type': 'contrast',
                'message': f'Increase headline size by {size_increase_pct}% to reach minimum legible height. Use bold fonts and high-contrast color combinations (e.g., black-on-yellow, white-on-blue).',
                'estimated_impact': f'Will improve recall by ~{min(20, size_increase_pct // 2)}%'
            })

        logger.info(f"Rule 3 triggered: MaxWordLegibility {max_word_legibility:.2f} < 0.7")

    # =========================================================================
    # RULE 4: Low Visual Salience (TopRegionSalience < 0.6)
    # =========================================================================
    if top_region_salience < 0.6:
        suggestions.append({
            'type': 'layout',
            'message': 'Move key element to visual power zone (lower-right or upper-left). Current layout has weak focal points. Eye-tracking studies show these zones capture 60% more attention on billboards.',
            'estimated_impact': f'Will improve recall by ~{int((0.6 - top_region_salience) * 30)}%'
        })
        logger.info(f"Rule 4 triggered: TopRegionSalience {top_region_salience:.2f} < 0.6")

    # =========================================================================
    # RULE 5: Logo Optimization (ALWAYS INCLUDE)
    # =========================================================================
    # This is always recommended as branding best practice
    logo_visible = ocr_result.get('logo_visible', False)

    if logo_visible:
        suggestions.append({
            'type': 'layout',
            'message': 'Increase logo size by 30-40% and position near headline. Logos should occupy 15-20% of billboard area for brand recognition. Place in upper-left or lower-right corner.',
            'estimated_impact': 'Will improve recall by ~8%'
        })
        logger.info("Rule 5: Logo optimization (logo present)")
    else:
        suggestions.append({
            'type': 'layout',
            'message': 'Add brand logo and increase size to occupy 15-20% of billboard area. Position near headline in upper-left or lower-right corner. Logos trigger instant brand recognition.',
            'estimated_impact': 'Will improve recall by ~12%'
        })
        logger.info("Rule 5: Logo optimization (no logo detected)")

    # =========================================================================
    # RULE 6: Contrast Enhancement (if legible but could be better)
    # =========================================================================
    if legible_words and max_word_legibility >= 0.7 and max_word_legibility < 0.85:
        suggestions.append({
            'type': 'contrast',
            'message': 'Enhance text-background contrast. Use complementary colors with luminance difference ≥50%. Recommended pairs: Black/Yellow, White/Blue, White/Red.',
            'estimated_impact': f'Will improve recall by ~{int((0.85 - max_word_legibility) * 15)}%'
        })
        logger.info(f"Rule 6 triggered: Moderate legibility {max_word_legibility:.2f}")

    # =========================================================================
    # RULE 7: Overall Weak Performance (recall < 50)
    # =========================================================================
    recall_score = recall_dict.get('score', 0)
    if recall_score < 50:
        suggestions.append({
            'type': 'layout',
            'message': f'Overall weak performance (score: {recall_score:.1f}/100). Apply billboard formula: 1 NUMBER + 1 VERB + 1 BRAND. Remove all non-essential elements. Use 80% of space for one dominant visual.',
            'estimated_impact': 'Will improve recall by ~30%'
        })
        logger.info(f"Rule 7 triggered: Low recall score {recall_score:.1f}")

    # =========================================================================
    # Prioritization
    # =========================================================================
    # Sort by estimated impact (extract percentage from string)
    def extract_impact(suggestion: Dict[str, str]) -> float:
        impact_str = suggestion['estimated_impact']
        # Extract first number from "Will improve recall by ~X%"
        import re
        match = re.search(r'~(\d+)%', impact_str)
        if match:
            return float(match.group(1))
        return 0.0

    suggestions.sort(key=extract_impact, reverse=True)

    # Limit to top 5 suggestions
    suggestions = suggestions[:5]

    logger.info(f"Generated {len(suggestions)} prioritized suggestions")

    return suggestions


# Backward compatibility wrapper for old API
def make_suggestions_legacy(
    recall_score: float,
    text_tokens: List[Dict[str, Any]],
    salience_data: Dict[str, Any],
    env_params: Dict[str, Any]
) -> List[Dict[str, str]]:
    """
    Legacy API wrapper for backward compatibility.

    Args:
        recall_score: Overall recall score (0-100)
        text_tokens: OCR text tokens
        salience_data: Salience analysis results
        env_params: Environment parameters

    Returns:
        List of suggestions with old format
    """
    # Convert to new format
    recall_dict = {
        'score': recall_score,
        '_components': {
            'max_word_legibility': max(t.get('confidence', 0) for t in text_tokens if t.get('legible', False)) if text_tokens else 0,
            'top_region_salience': max((r.get('salience_score', 0) for r in salience_data.get('hotspot_regions', [])), default=0)
        }
    }

    ocr_result = {
        'words_detected': text_tokens,
        'logo_visible': False
    }

    # Call new API
    suggestions = make_suggestions(recall_dict, ocr_result, salience_data)

    # Convert to old format (add category and priority for compatibility)
    for suggestion in suggestions:
        # Map type to category
        type_to_category = {
            'copy': 'Message Simplicity',
            'contrast': 'Text Legibility',
            'layout': 'Visual Layout'
        }
        suggestion['category'] = type_to_category.get(suggestion['type'], 'General')

        # Assign priority based on estimated impact
        impact_value = float(''.join(filter(str.isdigit, suggestion['estimated_impact'])))
        if impact_value >= 20:
            suggestion['priority'] = 'high'
        elif impact_value >= 10:
            suggestion['priority'] = 'medium'
        else:
            suggestion['priority'] = 'low'

        # Rename fields for old API
        suggestion['description'] = suggestion['message']
        suggestion['impact_estimate'] = suggestion['estimated_impact']

    return suggestions
