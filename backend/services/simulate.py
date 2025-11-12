"""
Motion blur simulation for highway viewing conditions
"""
import cv2
import numpy as np
from pathlib import Path


def simulate_view(
    image_path: str,
    speed_kmh: float,
    view_distance_m: float,
    dwell_sec: float,
    lighting: str
) -> str:
    """
    Simulate how an ad appears to a driver at highway speed

    Args:
        image_path: Path to original image
        speed_kmh: Vehicle speed in km/h (60-140)
        view_distance_m: Viewing distance in meters (20-60)
        dwell_sec: Time in view (0.5-2.0 seconds)
        lighting: Lighting condition (day/dusk/night)

    Returns:
        Path to simulated view image
    """
    # Load image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")

    # Calculate motion blur intensity based on speed and dwell time
    # Higher speed = more blur, longer dwell = less blur per frame
    blur_intensity = int((speed_kmh / 30) * (1.0 / dwell_sec) * 5)
    blur_intensity = max(1, min(blur_intensity, 50))  # Clamp between 1-50

    # Apply directional motion blur (horizontal for highway motion)
    kernel_size = blur_intensity
    kernel = np.zeros((kernel_size, kernel_size))
    kernel[int((kernel_size - 1) / 2), :] = np.ones(kernel_size)
    kernel = kernel / kernel_size

    blurred = cv2.filter2D(img, -1, kernel)

    # Apply distance-based blur (gaussian for depth of field)
    # More distant = more blur
    distance_blur = int((view_distance_m / 20) * 5)
    if distance_blur > 1:
        blurred = cv2.GaussianBlur(blurred, (distance_blur * 2 + 1, distance_blur * 2 + 1), 0)

    # Adjust for lighting conditions
    if lighting == "dusk":
        # Reduce brightness by 30%
        blurred = cv2.convertScaleAbs(blurred, alpha=0.7, beta=0)
    elif lighting == "night":
        # Reduce brightness by 60%, increase contrast slightly
        blurred = cv2.convertScaleAbs(blurred, alpha=0.5, beta=-20)

    # Save simulated view
    output_path = str(Path(image_path).parent / f"simulated_{Path(image_path).name}")
    cv2.imwrite(output_path, blurred)

    return output_path
