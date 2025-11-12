"""
Visual salience analysis using attention models
"""

import cv2
import numpy as np
import torch
from pathlib import Path
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


def analyze_salience(
    image_path: str,
    job_id: str,
    output_dir: str
) -> Dict[str, Any]:
    """
    Analyze visual salience to predict where viewers' attention will be drawn.

    Args:
        image_path: Path to simulated image
        job_id: Unique job identifier
        output_dir: Directory to save heatmap

    Returns:
        Dictionary with salience data including heatmap URL and attention metrics
    """
    logger.info(f"Analyzing salience for job {job_id}")

    try:
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image from {image_path}")

        # Convert to grayscale for saliency analysis
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Create a simple saliency map using gradient-based approach
        # In production, use more sophisticated models (e.g., DeepGaze)
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=5)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=5)
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)

        # Normalize to 0-255
        saliency_map = cv2.normalize(gradient_magnitude, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

        # Apply Gaussian blur to smooth the saliency map
        saliency_map = cv2.GaussianBlur(saliency_map, (21, 21), 0)

        # Create heatmap overlay
        heatmap = cv2.applyColorMap(saliency_map, cv2.COLORMAP_JET)
        overlay = cv2.addWeighted(img, 0.6, heatmap, 0.4, 0)

        # Save heatmap
        heatmap_path = Path(output_dir) / f"{job_id}_heatmap.jpg"
        cv2.imwrite(str(heatmap_path), overlay)

        # Calculate attention score (0-100)
        # Higher values indicate more visual interest
        mean_salience = np.mean(saliency_map)
        std_salience = np.std(saliency_map)
        attention_score = min(100, (mean_salience / 255 * 50) + (std_salience / 255 * 50))

        # Find hotspot regions (areas with high salience)
        threshold = np.percentile(saliency_map, 75)  # Top 25% most salient
        _, binary_mask = cv2.threshold(saliency_map, threshold, 255, cv2.THRESH_BINARY)

        # Find contours for hotspot regions
        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        hotspot_regions = []
        for i, contour in enumerate(contours[:5]):  # Top 5 hotspots
            x, y, w, h = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)

            if area > 100:  # Filter out tiny regions
                hotspot_regions.append({
                    'id': i,
                    'bbox': [int(x), int(y), int(w), int(h)],
                    'area': float(area),
                    'intensity': float(np.mean(saliency_map[y:y+h, x:x+w]))
                })

        logger.info(f"Salience analysis complete. Found {len(hotspot_regions)} hotspot regions")

        return {
            'heatmap_url': f"/files/{job_id}_heatmap.jpg",
            'attention_score': float(attention_score),
            'hotspot_regions': hotspot_regions
        }

    except Exception as e:
        logger.error(f"Error during salience analysis: {str(e)}")
        # Return default values on error
        return {
            'heatmap_url': '',
            'attention_score': 0.0,
            'hotspot_regions': []
        }
