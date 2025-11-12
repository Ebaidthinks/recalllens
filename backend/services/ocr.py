"""
Text extraction using OCR with legibility analysis
"""

from paddleocr import PaddleOCR
from typing import List, Dict, Any
import logging
import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Initialize PaddleOCR
ocr = None


def get_ocr_model():
    """Lazy load OCR model"""
    global ocr
    if ocr is None:
        ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
    return ocr


def extract_text_tokens(image_path: str) -> List[Dict[str, Any]]:
    """
    Extract text from image using OCR and analyze legibility.

    Args:
        image_path: Path to image (simulated view)

    Returns:
        List of text tokens with legibility information
    """
    logger.info(f"Extracting text from {image_path}")

    try:
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image from {image_path}")

        # Get OCR model
        ocr_model = get_ocr_model()

        # Run OCR
        result = ocr_model.ocr(image_path, cls=True)

        tokens = []

        if result and result[0]:
            for line in result[0]:
                # Extract bounding box and text info
                bbox = line[0]
                text_info = line[1]
                text = text_info[0]
                confidence = text_info[1]

                # Convert bbox to flat list of integers
                bbox_flat = [int(coord) for point in bbox for coord in point]

                # Determine legibility based on confidence and text length
                # Text is legible if confidence > 0.7 and length >= 2
                legible = confidence > 0.7 and len(text.strip()) >= 2

                tokens.append({
                    'text': text,
                    'confidence': float(confidence),
                    'bbox': bbox_flat,
                    'legible': legible
                })

        logger.info(f"Extracted {len(tokens)} text tokens")
        return tokens

    except Exception as e:
        logger.error(f"Error during OCR: {str(e)}")
        # Return empty list on error
        return []
