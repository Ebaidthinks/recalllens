"""
Text extraction using PaddleOCR with Arabic + English support and legibility analysis
"""

from paddleocr import PaddleOCR
from typing import List, Dict, Any, Union
import logging
import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Initialize PaddleOCR with multi-language support
ocr_models = {}


def get_ocr_model(lang: str = 'en') -> PaddleOCR:
    """
    Lazy load OCR model for specified language.

    Args:
        lang: Language code ('en', 'ar', or 'arabic_english' for both)

    Returns:
        PaddleOCR model instance
    """
    global ocr_models

    if lang not in ocr_models:
        logger.info(f"Initializing PaddleOCR for language: {lang}")

        # For Arabic + English support, we'll use a mixed approach
        # PaddleOCR supports multilingual detection
        if lang == 'arabic_english':
            # Use multilingual model that supports both Arabic and Latin scripts
            ocr_models[lang] = PaddleOCR(
                use_angle_cls=True,
                lang='en',  # Base model
                show_log=False,
                use_gpu=False,
                det_db_thresh=0.3,  # Lower threshold for better detection
                det_db_box_thresh=0.5
            )
        else:
            ocr_models[lang] = PaddleOCR(
                use_angle_cls=True,
                lang=lang,
                show_log=False,
                use_gpu=False
            )

    return ocr_models[lang]


def _is_arabic_char(char: str) -> bool:
    """
    Check if a character is Arabic.

    Args:
        char: Single character

    Returns:
        True if Arabic, False otherwise
    """
    code = ord(char)
    return ((0x0600 <= code <= 0x06FF) or  # Arabic
            (0x0750 <= code <= 0x077F) or  # Arabic Supplement
            (0x08A0 <= code <= 0x08FF) or  # Arabic Extended-A
            (0xFB50 <= code <= 0xFDFF) or  # Arabic Presentation Forms-A
            (0xFE70 <= code <= 0xFEFF))    # Arabic Presentation Forms-B


def _is_arabic_numeral(char: str) -> bool:
    """
    Check if a character is an Arabic-Indic numeral (٠-٩).

    Args:
        char: Single character

    Returns:
        True if Arabic numeral, False otherwise
    """
    code = ord(char)
    return 0x0660 <= code <= 0x0669  # Arabic-Indic digits ٠-٩


def _is_latin_char(char: str) -> bool:
    """
    Check if a character is Latin script (English).

    Args:
        char: Single character

    Returns:
        True if Latin, False otherwise
    """
    code = ord(char)
    return ((0x0041 <= code <= 0x005A) or  # A-Z
            (0x0061 <= code <= 0x007A) or  # a-z
            (0x0030 <= code <= 0x0039))    # 0-9


def _analyze_text_language(text: str) -> Dict[str, Any]:
    """
    Analyze language composition of text (Arabic vs English).

    Common in Dubai billboards to have mixed Arabic/English text.

    Args:
        text: Text string to analyze

    Returns:
        Dictionary with language analysis:
        {
            'direction': 'rtl' or 'ltr',
            'arabic_percentage': float (0-100),
            'english_percentage': float (0-100),
            'has_arabic_numerals': bool,
            'language_mix': 'arabic_dominant' | 'english_dominant' | 'mixed' | 'other'
        }
    """
    if not text:
        return {
            'direction': 'ltr',
            'arabic_percentage': 0.0,
            'english_percentage': 0.0,
            'has_arabic_numerals': False,
            'language_mix': 'other'
        }

    arabic_chars = 0
    latin_chars = 0
    arabic_numerals = 0
    total_chars = 0

    for char in text:
        if char.isspace():  # Skip whitespace
            continue

        total_chars += 1

        if _is_arabic_char(char):
            arabic_chars += 1
        elif _is_arabic_numeral(char):
            arabic_numerals += 1
            arabic_chars += 1  # Count numerals as Arabic
        elif _is_latin_char(char):
            latin_chars += 1

    if total_chars == 0:
        total_chars = 1  # Avoid division by zero

    arabic_pct = (arabic_chars / total_chars) * 100
    english_pct = (latin_chars / total_chars) * 100

    # Determine direction (RTL if more than 30% Arabic)
    direction = 'rtl' if arabic_pct > 30 else 'ltr'

    # Determine language mix
    if arabic_pct > 70:
        language_mix = 'arabic_dominant'
    elif english_pct > 70:
        language_mix = 'english_dominant'
    elif arabic_pct > 20 and english_pct > 20:
        language_mix = 'mixed'  # Common in Dubai: "SALE تخفيضات"
    else:
        language_mix = 'other'

    return {
        'direction': direction,
        'arabic_percentage': arabic_pct,
        'english_percentage': english_pct,
        'has_arabic_numerals': arabic_numerals > 0,
        'language_mix': language_mix
    }


def _detect_text_direction(text: str) -> str:
    """
    Detect if text is RTL (Arabic/Hebrew) or LTR.

    NOTE: This function is kept for backward compatibility.
    Use _analyze_text_language() for more detailed analysis.

    Args:
        text: Text string to analyze

    Returns:
        'rtl' or 'ltr'
    """
    analysis = _analyze_text_language(text)
    return analysis['direction']


def _calculate_bbox_height(bbox: List[List[int]]) -> int:
    """
    Calculate height of bounding box in pixels.

    Args:
        bbox: Bounding box as list of 4 points [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]

    Returns:
        Height in pixels
    """
    # Calculate height as average of left and right side heights
    left_height = abs(bbox[3][1] - bbox[0][1])
    right_height = abs(bbox[2][1] - bbox[1][1])
    avg_height = (left_height + right_height) / 2
    return int(avg_height)


def _calculate_bbox_width(bbox: List[List[int]]) -> int:
    """
    Calculate width of bounding box in pixels.

    Args:
        bbox: Bounding box as list of 4 points [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]

    Returns:
        Width in pixels
    """
    # Calculate width as average of top and bottom side widths
    top_width = abs(bbox[1][0] - bbox[0][0])
    bottom_width = abs(bbox[2][0] - bbox[3][0])
    avg_width = (top_width + bottom_width) / 2
    return int(avg_width)


def extract_text_tokens(frames: Union[List[np.ndarray], np.ndarray]) -> Dict[str, Any]:
    """
    Extract text from frames using OCR with Arabic + English support.

    Analyzes the middle frame for text detection, evaluates legibility based on
    confidence score and text height, and handles RTL (Arabic) text.

    Args:
        frames: List of frame arrays or single frame array from simulation

    Returns:
        Dictionary with structure:
        {
            "words_detected": [
                {"text": str, "bbox": [x,y,w,h], "confidence": float, "legible": bool, "direction": str},
                ...
            ],
            "logo_visible": bool,
            "brand_color_match": float
        }
    """
    logger.info("Starting OCR text extraction")

    try:
        # Handle both list of frames and single frame
        if isinstance(frames, list):
            if not frames:
                logger.warning("Empty frames list provided")
                return _empty_result()

            # Use middle frame for OCR
            middle_idx = len(frames) // 2
            frame = frames[middle_idx]
            logger.info(f"Using middle frame (index {middle_idx} of {len(frames)})")
        else:
            # Single frame provided
            frame = frames
            logger.info("Processing single frame")

        # Validate frame
        if frame is None or frame.size == 0:
            logger.warning("Invalid frame provided")
            return _empty_result()

        # Get OCR model with Arabic + English support
        ocr_model = get_ocr_model('arabic_english')

        # Run OCR on the frame
        # PaddleOCR expects numpy array or image path
        result = ocr_model.ocr(frame, cls=True)

        words_detected = []

        if result and result[0]:
            logger.info(f"OCR detected {len(result[0])} text regions")

            for detection in result[0]:
                # Extract bounding box and text info
                # Format: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                bbox = detection[0]
                text_info = detection[1]
                text = text_info[0]
                confidence = text_info[1]

                # Calculate bbox dimensions
                height = _calculate_bbox_height(bbox)
                width = _calculate_bbox_width(bbox)

                # Convert bbox to [x, y, w, h] format
                x = int(min(point[0] for point in bbox))
                y = int(min(point[1] for point in bbox))

                # Determine text direction (RTL for Arabic)
                direction = _detect_text_direction(text)

                # Legibility criteria:
                # 1. Confidence >= 0.7
                # 2. Height >= 22 pixels (minimum readable size at highway speeds)
                legible = confidence >= 0.7 and height >= 22

                # Log legibility analysis
                logger.debug(
                    f"Text: '{text}' | Confidence: {confidence:.2f} | "
                    f"Height: {height}px | Legible: {legible} | Direction: {direction}"
                )

                words_detected.append({
                    'text': text,
                    'bbox': [x, y, width, height],
                    'confidence': float(confidence),
                    'legible': legible,
                    'direction': direction,
                    'height_px': height,
                    'width_px': width
                })
        else:
            logger.info("No text detected in frame")

        # Logo detection placeholder (not implemented yet)
        logo_visible = False
        brand_color_match = 0.0

        # Analyze overall language composition (useful for Dubai market)
        all_text = ' '.join([w['text'] for w in words_detected])
        language_analysis = _analyze_text_language(all_text)

        # Count Arabic vs English words
        arabic_words = sum(1 for w in words_detected if _analyze_text_language(w['text'])['language_mix'] in ['arabic_dominant', 'mixed'])
        english_words = sum(1 for w in words_detected if _analyze_text_language(w['text'])['language_mix'] == 'english_dominant')

        result = {
            'words_detected': words_detected,
            'logo_visible': logo_visible,
            'brand_color_match': brand_color_match,
            'language_analysis': {
                'overall_direction': language_analysis['direction'],
                'arabic_percentage': language_analysis['arabic_percentage'],
                'english_percentage': language_analysis['english_percentage'],
                'has_arabic_numerals': language_analysis['has_arabic_numerals'],
                'language_mix': language_analysis['language_mix'],
                'arabic_word_count': arabic_words,
                'english_word_count': english_words,
                'total_word_count': len(words_detected)
            }
        }

        logger.info(
            f"OCR complete: {len(words_detected)} words detected, "
            f"{sum(1 for w in words_detected if w['legible'])} legible | "
            f"Language: {language_analysis['language_mix']} "
            f"(AR:{language_analysis['arabic_percentage']:.0f}% EN:{language_analysis['english_percentage']:.0f}%)"
        )

        return result

    except Exception as e:
        logger.error(f"Error during OCR: {str(e)}", exc_info=True)
        return _empty_result()


def _empty_result() -> Dict[str, Any]:
    """
    Return empty result structure.

    Returns:
        Empty result dictionary
    """
    return {
        'words_detected': [],
        'logo_visible': False,
        'brand_color_match': 0.0,
        'language_analysis': {
            'overall_direction': 'ltr',
            'arabic_percentage': 0.0,
            'english_percentage': 0.0,
            'has_arabic_numerals': False,
            'language_mix': 'other',
            'arabic_word_count': 0,
            'english_word_count': 0,
            'total_word_count': 0
        }
    }


# Backward compatibility function for old API
def extract_text_tokens_from_path(image_path: str) -> Dict[str, Any]:
    """
    Extract text from image file path (backward compatibility).

    Args:
        image_path: Path to image file

    Returns:
        OCR result dictionary
    """
    logger.info(f"Loading image from path: {image_path}")

    # Load image
    img = cv2.imread(image_path)
    if img is None:
        logger.error(f"Could not load image from {image_path}")
        return _empty_result()

    # Use main extraction function
    return extract_text_tokens(img)
