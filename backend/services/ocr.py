"""
OCR and text token extraction
"""
from paddleocr import PaddleOCR
import cv2
from typing import List, Dict


# Initialize PaddleOCR once
ocr_engine = None


def get_ocr_engine():
    """Lazy load OCR engine"""
    global ocr_engine
    if ocr_engine is None:
        ocr_engine = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
    return ocr_engine


def extract_text_tokens(image_path: str) -> Dict:
    """
    Extract text tokens from image using OCR

    Args:
        image_path: Path to image file

    Returns:
        Dictionary with:
        - tokens: List of detected text strings
        - positions: List of bounding boxes [[x1,y1,x2,y2], ...]
        - confidences: List of confidence scores
        - legibility_score: Overall text readability (0-1)
    """
    # Load image
    img = cv2.imread(image_path)
    if img is None:
        return {
            "tokens": [],
            "positions": [],
            "confidences": [],
            "legibility_score": 0.0
        }

    # Run OCR
    ocr = get_ocr_engine()
    result = ocr.ocr(image_path, cls=True)

    tokens = []
    positions = []
    confidences = []

    if result and result[0]:
        for line in result[0]:
            if line:
                # line format: [bbox, (text, confidence)]
                bbox = line[0]
                text = line[1][0]
                conf = line[1][1]

                tokens.append(text)
                # Convert bbox to [x1, y1, x2, y2]
                x_coords = [p[0] for p in bbox]
                y_coords = [p[1] for p in bbox]
                positions.append([
                    min(x_coords),
                    min(y_coords),
                    max(x_coords),
                    max(y_coords)
                ])
                confidences.append(float(conf))

    # Calculate legibility score based on:
    # 1. Average confidence
    # 2. Number of tokens detected
    # 3. Text size relative to image
    if confidences:
        avg_confidence = sum(confidences) / len(confidences)
        token_count_score = min(len(tokens) / 10.0, 1.0)  # Normalize by expected count

        # Calculate average text area
        img_area = img.shape[0] * img.shape[1]
        text_areas = [(pos[2] - pos[0]) * (pos[3] - pos[1]) for pos in positions]
        avg_text_area = sum(text_areas) / len(text_areas) if text_areas else 0
        size_score = min(avg_text_area / (img_area * 0.01), 1.0)  # Text should be at least 1% of image

        legibility_score = (avg_confidence * 0.5 + token_count_score * 0.3 + size_score * 0.2)
    else:
        legibility_score = 0.0

    return {
        "tokens": tokens,
        "positions": positions,
        "confidences": confidences,
        "legibility_score": min(legibility_score, 1.0)
    }
