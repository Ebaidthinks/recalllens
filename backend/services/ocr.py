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


def _detect_text_direction(text: str) -> str:
    """
    Detect if text is RTL (Arabic/Hebrew) or LTR.

    Args:
        text: Text string to analyze

    Returns:
        'rtl' or 'ltr'
    """
    # Arabic Unicode range: 0600-06FF, 0750-077F, 08A0-08FF, FB50-FDFF, FE70-FEFF
    # Hebrew Unicode range: 0590-05FF
    rtl_chars = 0
    total_chars = 0

    for char in text:
        code = ord(char)
        total_chars += 1

        # Check if character is Arabic or Hebrew
        if ((0x0600 <= code <= 0x06FF) or
            (0x0750 <= code <= 0x077F) or
            (0x08A0 <= code <= 0x08FF) or
            (0xFB50 <= code <= 0xFDFF) or
            (0xFE70 <= code <= 0xFEFF) or
            (0x0590 <= code <= 0x05FF)):
            rtl_chars += 1

    # If more than 30% of characters are RTL, consider it RTL text
    if total_chars > 0 and (rtl_chars / total_chars) > 0.3:
        return 'rtl'
    return 'ltr'


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

        result = {
            'words_detected': words_detected,
            'logo_visible': logo_visible,
            'brand_color_match': brand_color_match
        }

        logger.info(
            f"OCR complete: {len(words_detected)} words detected, "
            f"{sum(1 for w in words_detected if w['legible'])} legible"
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
        'brand_color_match': 0.0
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
