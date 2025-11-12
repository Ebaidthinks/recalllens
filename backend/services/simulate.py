"""
Simulate driver view with motion blur and environmental effects
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def simulate_view(
    input_path: str,
    job_id: str,
    env_params: Dict[str, Any],
    output_dir: str
) -> str:
    """
    Simulate how a driver would see the ad based on speed, distance, and conditions.

    Args:
        input_path: Path to original image
        job_id: Unique job identifier
        env_params: Environment parameters (speed_kmh, view_distance_m, dwell_sec, lighting, phone_distraction)
        output_dir: Directory to save simulated image

    Returns:
        Path to simulated image
    """
    logger.info(f"Simulating view for job {job_id}")

    # Load image
    img = cv2.imread(input_path)
    if img is None:
        raise ValueError(f"Could not load image from {input_path}")

    # Extract parameters
    speed_kmh = env_params['speed_kmh']
    dwell_sec = env_params['dwell_sec']
    lighting = env_params['lighting']
    phone_distraction = env_params['phone_distraction']

    # Calculate motion blur based on speed and dwell time
    # Higher speed = more blur
    blur_amount = int((speed_kmh / 60) * 15)  # Scale blur with speed
    if blur_amount > 1:
        kernel_size = blur_amount if blur_amount % 2 == 1 else blur_amount + 1
        img = cv2.GaussianBlur(img, (kernel_size, kernel_size), 0)

    # Apply lighting effects
    if lighting == 'dusk':
        # Reduce brightness and add slight color tint
        img = cv2.convertScaleAbs(img, alpha=0.7, beta=-20)
    elif lighting == 'night':
        # Much darker with strong reduction
        img = cv2.convertScaleAbs(img, alpha=0.4, beta=-50)

    # Apply distraction effects (reduces clarity/focus)
    distraction_map = {'low': 0, 'med': 5, 'high': 10}
    distraction_blur = distraction_map.get(phone_distraction, 0)
    if distraction_blur > 0:
        img = cv2.GaussianBlur(img, (distraction_blur + 1, distraction_blur + 1), 0)

    # Add slight noise for realism
    noise = np.random.normal(0, 5, img.shape).astype(np.uint8)
    img = cv2.add(img, noise)

    # Save simulated image
    output_path = Path(output_dir) / f"{job_id}_simulated.jpg"
    cv2.imwrite(str(output_path), img)

    logger.info(f"Simulated image saved to {output_path}")
    return str(output_path)
