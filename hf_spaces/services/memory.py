"""
Memory recall computation - predicts what drivers will actually REMEMBER

Uses cognitive science principles and sigmoid-based scoring to estimate
memory encoding probability based on legibility, salience, and information density.
"""

from typing import Dict, Any, List
import numpy as np
import cv2
import logging

logger = logging.getLogger(__name__)


def _detect_dominant_color(image_path: str = None, image: np.ndarray = None) -> str:
    """
    Detect the dominant color in an image using K-means clustering.

    Args:
        image_path: Path to image file (optional)
        image: Image array (optional)

    Returns:
        Color name string (e.g., "Red", "Blue", "Yellow")
    """
    # Load image if path provided
    if image_path:
        img = cv2.imread(image_path)
    elif image is not None:
        img = image
    else:
        return "Unknown"

    if img is None:
        return "Unknown"

    # Resize for faster processing
    img = cv2.resize(img, (150, 150))

    # Reshape to list of pixels
    pixels = img.reshape(-1, 3).astype(np.float32)

    # Use K-means to find dominant colors (k=5)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    k = 5
    _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_PP_CENTERS)

    # Find most common cluster
    unique, counts = np.unique(labels, return_counts=True)
    dominant_cluster_idx = unique[np.argmax(counts)]
    dominant_color_bgr = centers[dominant_cluster_idx]

    # Convert BGR to RGB
    b, g, r = dominant_color_bgr

    # Map to color names based on RGB values
    color_name = _rgb_to_color_name(int(r), int(g), int(b))

    return color_name


def _rgb_to_color_name(r: int, g: int, b: int) -> str:
    """
    Convert RGB values to human-readable color name.

    Args:
        r, g, b: RGB color values (0-255)

    Returns:
        Color name string
    """
    # Define color ranges
    if r > 200 and g < 100 and b < 100:
        return "Red"
    elif r > 200 and g > 200 and b < 100:
        return "Yellow"
    elif r < 100 and g > 200 and b < 100:
        return "Green"
    elif r < 100 and g < 100 and b > 200:
        return "Blue"
    elif r > 200 and g > 150 and b < 100:
        return "Orange"
    elif r > 150 and g < 100 and b > 150:
        return "Purple"
    elif r > 200 and g > 200 and b > 200:
        return "White"
    elif r < 80 and g < 80 and b < 80:
        return "Black"
    elif r > 100 and g > 100 and b > 100 and r < 180:
        return "Gray"
    else:
        # Default to most dominant channel
        max_val = max(r, g, b)
        if max_val == r:
            return "Red"
        elif max_val == g:
            return "Green"
        else:
            return "Blue"


def compute_recall(
    ocr_result: Dict[str, Any],
    sal_result: Dict[str, Any],
    image_path: str = None
) -> Dict[str, Any]:
    """
    Compute predicted memory recall score using sigmoid-based model.

    This is the CORE ALGORITHM that predicts what drivers will actually remember.
    Uses explicit math based on cognitive psychology research.

    Args:
        ocr_result: OCR results dict with 'words_detected', 'logo_visible', etc.
        sal_result: Salience results dict with 'hotspot_regions', 'attention_score', etc.
        image_path: Optional path to image for color detection

    Returns:
        Dictionary with:
            - score: Overall recall probability (0-100)
            - memory_summary: Detailed breakdown of what will be remembered
    """
    logger.info("Computing memory recall score using sigmoid model")

    # Extract data
    words_detected = ocr_result.get('words_detected', [])
    logo_visible = ocr_result.get('logo_visible', False)
    hotspot_regions = sal_result.get('hotspot_regions', [])

    # ============================================================================
    # STEP 1: Calculate Component Scores (0-1 scale)
    # ============================================================================

    # Component 1: MaxWordLegibility
    # Definition: Highest confidence score among legible words
    # Rationale: If even ONE word is clearly readable, it anchors memory
    legible_words = [w for w in words_detected if w.get('legible', False)]

    if legible_words:
        max_word_legibility = max(w['confidence'] for w in legible_words)
    else:
        max_word_legibility = 0.0

    logger.info(f"MaxWordLegibility: {max_word_legibility:.3f}")

    # Component 2: TopRegionSalience
    # Definition: Salience score of the most visually salient region
    # Rationale: Eyes are drawn to salient regions first - these encode better
    if hotspot_regions:
        top_region_salience = max(region.get('salience_score', 0.0) for region in hotspot_regions)
    else:
        top_region_salience = 0.0

    logger.info(f"TopRegionSalience: {top_region_salience:.3f}")

    # Component 3: LogoPresence
    # Definition: Binary indicator of recognizable brand logo
    # Rationale: Logos trigger existing memory schemas (instant recognition)
    logo_presence = 1.0 if logo_visible else 0.0

    logger.info(f"LogoPresence: {logo_presence:.1f}")

    # Component 4: CopyDensityPenalty
    # Definition: Penalty for too many words (cognitive overload)
    # Formula: max(0, (word_count - 5) / 5)
    # Rationale: Working memory capacity is ~7±2 items; billboards should be <5 words
    word_count = len(words_detected)
    copy_density_penalty = max(0.0, (word_count - 5) / 5.0)

    logger.info(f"CopyDensityPenalty: {copy_density_penalty:.3f} (word_count={word_count})")

    # Component 5: LowContrastPenalty
    # Placeholder for future contrast analysis
    low_contrast_penalty = 0.0

    logger.info(f"LowContrastPenalty: {low_contrast_penalty:.3f} (placeholder)")

    # ============================================================================
    # STEP 2: Compute Recall Score using Sigmoid Function
    # ============================================================================

    # Sigmoid formula:
    # score = 100 / (1 + exp(-z))
    #
    # where z = linear combination of weighted components
    #
    # Weights (tuned based on cognitive psychology literature):
    #   +1.2 × MaxWordLegibility    (dominant factor: can they READ it?)
    #   +0.8 × TopRegionSalience    (strong factor: does it GRAB attention?)
    #   +0.6 × LogoPresence         (moderate boost: brand recognition)
    #   -0.7 × CopyDensityPenalty   (penalty: too much text = cognitive overload)
    #   -0.5 × LowContrastPenalty   (penalty: hard to see = hard to remember)

    z = (
        1.2 * max_word_legibility +
        0.8 * top_region_salience +
        0.6 * logo_presence -
        0.7 * copy_density_penalty -
        0.5 * low_contrast_penalty
    )

    logger.info(f"Linear combination z: {z:.3f}")

    # Apply sigmoid transformation
    # This maps z ∈ (-∞, +∞) to score ∈ (0, 100)
    recall_score = 100.0 / (1.0 + np.exp(-z))

    logger.info(f"Recall Score (sigmoid): {recall_score:.2f}")

    # ============================================================================
    # STEP 3: Generate Predicted Gist (what driver will actually remember)
    # ============================================================================

    # Detect dominant color
    if image_path:
        dominant_color = _detect_dominant_color(image_path=image_path)
    else:
        dominant_color = "Colorful"

    # Get top 2 legible words (sorted by confidence)
    if legible_words:
        sorted_legible = sorted(legible_words, key=lambda w: w['confidence'], reverse=True)
        top_words = [w['text'] for w in sorted_legible[:2]]
    else:
        top_words = []

    # Format: "COLOR — WORD1 — WORD2"
    if len(top_words) >= 2:
        predicted_gist = f"{dominant_color} — {top_words[0]} — {top_words[1]}"
    elif len(top_words) == 1:
        predicted_gist = f"{dominant_color} — {top_words[0]}"
    else:
        predicted_gist = f"{dominant_color} billboard (no legible text)"

    logger.info(f"Predicted gist: {predicted_gist}")

    # ============================================================================
    # STEP 4: Generate Elements Encoded (what gets into memory)
    # ============================================================================

    elements_encoded = []

    # Add color to memory
    elements_encoded.append(f"{dominant_color.lower()} background")

    # Add legible words (up to 3, based on recall score)
    if recall_score >= 70:
        num_words_encoded = min(3, len(legible_words))
    elif recall_score >= 40:
        num_words_encoded = min(2, len(legible_words))
    else:
        num_words_encoded = min(1, len(legible_words))

    for word in top_words[:num_words_encoded]:
        elements_encoded.append(word.lower())

    # Add logo if present
    if logo_visible:
        elements_encoded.append("brand logo")

    logger.info(f"Elements encoded: {elements_encoded}")

    # ============================================================================
    # STEP 5: Calculate Confusion Risk
    # ============================================================================

    # Confusion risk: probability of misremembering or mixing up elements
    # Higher risk when:
    # - Many words (high density)
    # - Low legibility
    # - Low salience

    confusion_factors = []

    # Factor 1: Copy density (more words = more confusion)
    if word_count > 5:
        confusion_factors.append(0.15 * (word_count - 5))

    # Factor 2: Low legibility (can't read = will guess wrong)
    if max_word_legibility < 0.7:
        confusion_factors.append(0.3 * (0.7 - max_word_legibility))

    # Factor 3: Low salience (didn't look = might misremember)
    if top_region_salience < 0.5:
        confusion_factors.append(0.2 * (0.5 - top_region_salience))

    confusion_risk = min(1.0, sum(confusion_factors))

    logger.info(f"Confusion risk: {confusion_risk:.3f}")

    # ============================================================================
    # STEP 6: Return Results
    # ============================================================================

    return {
        'score': float(recall_score),
        'memory_summary': {
            'predicted_gist': predicted_gist,
            'elements_encoded': elements_encoded,
            'confusion_risk': float(confusion_risk)
        },
        # Additional debugging info
        '_components': {
            'max_word_legibility': float(max_word_legibility),
            'top_region_salience': float(top_region_salience),
            'logo_presence': float(logo_presence),
            'copy_density_penalty': float(copy_density_penalty),
            'low_contrast_penalty': float(low_contrast_penalty),
            'z_score': float(z)
        }
    }


# Backward compatibility wrapper for old API
def compute_recall_legacy(
    text_tokens: List[Dict[str, Any]],
    salience_data: Dict[str, Any],
    env_params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Legacy API wrapper for backward compatibility.

    Args:
        text_tokens: List of text tokens
        salience_data: Salience analysis results
        env_params: Environment parameters (not used in new model)

    Returns:
        Results in old format with recall_score and predicted_gist
    """
    # Convert to new format
    ocr_result = {
        'words_detected': text_tokens,
        'logo_visible': False,
        'brand_color_match': 0.0
    }

    # Call new API
    result = compute_recall(ocr_result, salience_data)

    # Convert to old format
    return {
        'recall_score': result['score'],
        'predicted_gist': result['memory_summary']['predicted_gist'],
        'retention_factors': result.get('_components', {})
    }
