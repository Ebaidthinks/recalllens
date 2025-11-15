"""
Simulate driver view with motion blur and environmental effects using realistic CV techniques

Includes Dubai-specific presets for common highways and lighting conditions.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


# Dubai Road Presets
# These configurations are calibrated for typical viewing conditions on Dubai highways
DUBAI_ROAD_PRESETS = {
    'szr': {
        'name': 'Sheikh Zayed Road (SZR)',
        'speed_kmh': 120.0,
        'view_distance_m': 40.0,
        'dwell_sec': 0.8,  # Brief due to high speed
        'lighting': 'dubai_day',
        'phone_distraction': 'med',
        'description': 'High-speed highway with intense sun glare and long viewing distances'
    },
    'al_khail': {
        'name': 'Al Khail Road',
        'speed_kmh': 100.0,
        'view_distance_m': 35.0,
        'dwell_sec': 1.0,
        'lighting': 'dubai_day',
        'phone_distraction': 'low',
        'description': 'Major highway with moderate speed and good visibility'
    },
    'jbr': {
        'name': 'JBR Urban (Jumeirah Beach)',
        'speed_kmh': 60.0,
        'view_distance_m': 25.0,
        'dwell_sec': 1.5,
        'lighting': 'day',
        'phone_distraction': 'low',
        'description': 'Urban setting with slower traffic and closer viewing'
    },
    'marina': {
        'name': 'Dubai Marina',
        'speed_kmh': 60.0,
        'view_distance_m': 20.0,
        'dwell_sec': 1.8,
        'lighting': 'day',
        'phone_distraction': 'med',
        'description': 'Dense urban area with pedestrians and heavy traffic'
    }
}


def get_dubai_preset(preset_name: str) -> Optional[Dict[str, Any]]:
    """
    Get Dubai road preset configuration.

    Args:
        preset_name: Name of preset ('szr', 'al_khail', 'jbr', 'marina')

    Returns:
        Dictionary with preset parameters, or None if not found
    """
    return DUBAI_ROAD_PRESETS.get(preset_name.lower())


def list_dubai_presets() -> List[Dict[str, Any]]:
    """
    List all available Dubai road presets.

    Returns:
        List of preset configurations with metadata
    """
    return [{'id': key, **value} for key, value in DUBAI_ROAD_PRESETS.items()]


def _motion_blur(img: np.ndarray, speed_kmh: float) -> np.ndarray:
    """
    Apply horizontal motion blur to simulate high-speed viewing.

    The blur kernel length is proportional to speed, simulating the
    streak effect of objects passing by at high velocity.

    Args:
        img: Input image (BGR)
        speed_kmh: Vehicle speed in km/h

    Returns:
        Motion-blurred image
    """
    # Calculate kernel length based on speed
    # At 60 km/h: 6 pixels, at 120 km/h: 12 pixels, etc.
    kernel_length = max(3, int(speed_kmh * 0.1))

    # Ensure odd kernel size for symmetric blur
    if kernel_length % 2 == 0:
        kernel_length += 1

    # Create horizontal motion blur kernel
    # All weight is distributed horizontally (motion direction)
    kernel = np.zeros((kernel_length, kernel_length))
    kernel[kernel_length // 2, :] = np.ones(kernel_length)
    kernel = kernel / kernel_length  # Normalize to sum to 1

    # Apply the blur using 2D convolution
    blurred = cv2.filter2D(img, -1, kernel)

    logger.debug(f"Applied motion blur with kernel length {kernel_length} pixels")
    return blurred


def _distance_scale(
    img: np.ndarray,
    view_distance_m: float,
    panel_height_m: float = 4.0
) -> np.ndarray:
    """
    Scale image to simulate viewing distance based on angular size.

    Uses the principle that apparent size decreases with distance.
    The angular size θ ≈ object_size / distance for small angles.

    Args:
        img: Input image (BGR)
        view_distance_m: Viewing distance in meters
        panel_height_m: Real-world height of the billboard panel in meters

    Returns:
        Scaled image simulating the apparent size at given distance
    """
    height, width = img.shape[:2]

    # Calculate pixels per meter in the original image
    pixels_per_meter = height / panel_height_m

    # Reference distance where image appears "normal" (close-up)
    reference_distance_m = 5.0  # Assume image is at 5m reference

    # Calculate scaling factor based on angular size
    # Angular size is inversely proportional to distance
    scale_factor = reference_distance_m / view_distance_m

    # Clamp scale factor to reasonable bounds
    scale_factor = max(0.1, min(1.0, scale_factor))

    # Calculate new dimensions
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)

    # Resize using high-quality interpolation
    scaled = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)

    # Pad back to original size (billboard in distance appears smaller)
    # Center the scaled image in a canvas of original size
    canvas = np.zeros_like(img)
    y_offset = (height - new_height) // 2
    x_offset = (width - new_width) // 2
    canvas[y_offset:y_offset+new_height, x_offset:x_offset+new_width] = scaled

    logger.debug(f"Scaled to {scale_factor:.2f}x for {view_distance_m}m viewing distance")
    return canvas


def _atmospheric_effect(img: np.ndarray, lighting: str) -> np.ndarray:
    """
    Apply atmospheric and lighting effects based on time of day.

    Simulates how lighting conditions affect color perception and contrast.
    Includes Dubai-specific lighting conditions with intense sun and glare.

    Args:
        img: Input image (BGR)
        lighting: Lighting condition ('day', 'dusk', 'night', 'dubai_day', 'dubai_dusk', 'dubai_night')

    Returns:
        Image with lighting effects applied
    """
    result = img.copy().astype(np.float32)

    if lighting == 'day':
        # Day: Slight atmospheric haze from distance
        # Minimal Gaussian blur to simulate air turbulence
        result = cv2.GaussianBlur(result, (3, 3), 0.5)

    elif lighting == 'dubai_day':
        # Dubai Day: Intense sunlight with high glare and heat haze
        # Characteristic of desert climate with strong direct sunlight

        # Increase brightness (intense sun)
        result = result * 1.15

        # Add glare effect - blow out highlights (overexposure simulation)
        # Areas above threshold get washed out
        bright_mask = result > 200
        result[bright_mask] = result[bright_mask] * 1.2

        # Warm color shift (desert sun has warm temperature)
        result[:, :, 2] = result[:, :, 2] * 1.1  # Increase red
        result[:, :, 1] = result[:, :, 1] * 1.05  # Slight increase green
        result[:, :, 0] = result[:, :, 0] * 0.92  # Decrease blue

        # Heat haze - stronger atmospheric blur
        result = cv2.GaussianBlur(result, (5, 5), 0.8)

        # Reduce contrast slightly (atmospheric scattering)
        mean_val = np.mean(result)
        result = (result - mean_val) * 0.9 + mean_val

    elif lighting == 'dusk':
        # Dusk: Warm color temperature + reduced brightness + more haze
        # Shift color balance toward warm tones (golden hour)
        # Increase red and decrease blue channels
        result[:, :, 2] = result[:, :, 2] * 1.15  # Red channel (BGR)
        result[:, :, 0] = result[:, :, 0] * 0.85  # Blue channel

        # Reduce overall brightness
        result = result * 0.7

        # More atmospheric blur
        result = cv2.GaussianBlur(result, (5, 5), 1.0)

    elif lighting == 'dubai_dusk':
        # Dubai Dusk: Golden hour with warm tones, reduced but still good visibility
        # Dubai's desert location creates spectacular golden hour lighting

        # Strong warm color shift (golden hour)
        result[:, :, 2] = result[:, :, 2] * 1.25  # Strong red boost
        result[:, :, 1] = result[:, :, 1] * 1.15  # Green boost
        result[:, :, 0] = result[:, :, 0] * 0.75  # Strong blue reduction

        # Moderate brightness reduction (not as dark as typical dusk)
        result = result * 0.75

        # Soft atmospheric blur
        result = cv2.GaussianBlur(result, (5, 5), 0.8)

        # Slightly reduced contrast (softer light)
        mean_val = np.mean(result)
        result = (result - mean_val) * 0.85 + mean_val

    elif lighting == 'night':
        # Night: Very dark, high contrast, blue shift
        # Reduce brightness significantly
        result = result * 0.35

        # Increase contrast (expand dynamic range)
        mean_val = np.mean(result)
        result = (result - mean_val) * 1.5 + mean_val

        # Slight blue shift (scotopic vision)
        result[:, :, 0] = result[:, :, 0] * 1.1  # Blue channel

        # More blur due to low light and pupil dilation
        result = cv2.GaussianBlur(result, (5, 5), 1.2)

    elif lighting == 'dubai_night':
        # Dubai Night: LED billboard compensation, still relatively bright
        # Dubai billboards have high-brightness LEDs that remain visible at night

        # Less brightness reduction than typical night (LED billboards are bright)
        result = result * 0.50  # Less aggressive than normal night (0.35)

        # LED screens have high contrast and vivid colors
        mean_val = np.mean(result)
        result = (result - mean_val) * 1.3 + mean_val

        # Slight cool shift (LED white balance)
        result[:, :, 0] = result[:, :, 0] * 1.05  # Slight blue boost

        # Moderate blur (city lighting provides ambient illumination)
        result = cv2.GaussianBlur(result, (3, 3), 0.8)

    # Clip values to valid range and convert back to uint8
    result = np.clip(result, 0, 255).astype(np.uint8)

    logger.debug(f"Applied {lighting} lighting effects")
    return result


def _add_distraction_effect(img: np.ndarray, phone_distraction: str) -> np.ndarray:
    """
    Simulate reduced attention due to phone distraction.

    Args:
        img: Input image (BGR)
        phone_distraction: Distraction level ('low', 'med', 'high')

    Returns:
        Image with distraction effects
    """
    if phone_distraction == 'low':
        # Minimal effect - slight peripheral blur
        return cv2.GaussianBlur(img, (3, 3), 0.5)
    elif phone_distraction == 'med':
        # Moderate effect - noticeable blur from divided attention
        return cv2.GaussianBlur(img, (7, 7), 1.5)
    elif phone_distraction == 'high':
        # High effect - significant blur, reduced contrast
        blurred = cv2.GaussianBlur(img, (11, 11), 2.5)
        # Reduce contrast (compressed dynamic range)
        mean_val = np.mean(blurred)
        result = (blurred - mean_val) * 0.7 + mean_val
        return np.clip(result, 0, 255).astype(np.uint8)

    return img


def simulate_view(
    input_path: str,
    env_dict: Dict[str, Any],
    job_id: str,
    output_dir: str
) -> Dict[str, Any]:
    """
    Simulate how a driver would see the ad at highway speeds with scientific accuracy.

    Generates a sequence of frames over the dwell period, applying:
    - Distance-based scaling (angular size)
    - Motion blur from vehicle speed
    - Atmospheric/lighting effects
    - Micro-saccades (eye jitter)
    - Distraction effects

    Args:
        input_path: Path to original image
        env_dict: Environment parameters with keys:
            - speed_kmh: Vehicle speed (60-140 km/h)
            - view_distance_m: Viewing distance (20-60 m)
            - dwell_sec: Viewing duration (0.5-2.0 s)
            - lighting: 'day', 'dusk', or 'night'
            - phone_distraction: 'low', 'med', or 'high'
        job_id: Unique job identifier
        output_dir: Directory to save outputs

    Returns:
        Dictionary with:
            - frames: List of frame arrays
            - video_path: Path to saved MP4 video
            - representative_frame_path: Path to single representative frame (for OCR)
    """
    logger.info(f"Simulating driver view for job {job_id}")

    # Load original image
    img = cv2.imread(input_path)
    if img is None:
        raise ValueError(f"Could not load image from {input_path}")

    # Extract parameters
    speed_kmh = env_dict['speed_kmh']
    view_distance_m = env_dict['view_distance_m']
    dwell_sec = env_dict['dwell_sec']
    lighting = env_dict['lighting']
    phone_distraction = env_dict['phone_distraction']

    logger.info(f"Simulation params: speed={speed_kmh}km/h, distance={view_distance_m}m, "
                f"dwell={dwell_sec}s, lighting={lighting}, distraction={phone_distraction}")

    # Step 1: Apply distance scaling (angular size reduction)
    img_scaled = _distance_scale(img, view_distance_m)

    # Step 2: Apply atmospheric/lighting effects
    img_lit = _atmospheric_effect(img_scaled, lighting)

    # Step 3: Apply distraction effect
    img_distracted = _add_distraction_effect(img_lit, phone_distraction)

    # Step 4: Generate frame sequence with motion blur and micro-saccades
    num_frames = 12  # Generate 12 frames over dwell period
    frames = []

    for i in range(num_frames):
        frame = img_distracted.copy()

        # Apply motion blur (constant across all frames)
        frame = _motion_blur(frame, speed_kmh)

        # Add micro-saccades (small random eye movements)
        # Humans make small involuntary eye movements even when fixating
        # Jitter amplitude: 1-3 pixels (realistic for brief fixations)
        jitter_x = np.random.randint(-2, 3)
        jitter_y = np.random.randint(-2, 3)

        # Apply jitter using affine transformation
        if jitter_x != 0 or jitter_y != 0:
            M = np.float32([[1, 0, jitter_x], [0, 1, jitter_y]])
            frame = cv2.warpAffine(frame, M, (frame.shape[1], frame.shape[0]))

        # Add slight per-frame noise (photoreceptor noise)
        noise = np.random.normal(0, 2, frame.shape).astype(np.float32)
        frame = np.clip(frame.astype(np.float32) + noise, 0, 255).astype(np.uint8)

        frames.append(frame)

    logger.info(f"Generated {num_frames} frames with motion blur and micro-saccades")

    # Step 5: Save representative frame (middle frame for OCR analysis)
    representative_idx = num_frames // 2
    representative_frame = frames[representative_idx]
    representative_path = Path(output_dir) / f"{job_id}_simulated.jpg"
    cv2.imwrite(str(representative_path), representative_frame)
    logger.info(f"Saved representative frame: {representative_path}")

    # Step 6: Create video from frames
    video_path = Path(output_dir) / f"{job_id}_simulation.mp4"
    height, width = frames[0].shape[:2]

    # Calculate FPS to match dwell time
    fps = num_frames / dwell_sec

    # Use H.264 codec for compatibility
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(
        str(video_path),
        fourcc,
        fps,
        (width, height)
    )

    if not video_writer.isOpened():
        logger.warning("Could not create video writer, skipping video generation")
        video_path_str = None
    else:
        for frame in frames:
            video_writer.write(frame)
        video_writer.release()
        logger.info(f"Saved simulation video: {video_path}")
        video_path_str = str(video_path)

    # Return comprehensive results
    return {
        'frames': frames,
        'video_path': video_path_str,
        'representative_frame_path': str(representative_path),
        'num_frames': num_frames,
        'fps': fps
    }
