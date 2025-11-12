"""
Visual salience analysis using ResNet50 + Grad-CAM for attention prediction
"""

import cv2
import numpy as np
import torch
import torchvision.models as models
import torchvision.transforms as transforms
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget
from pytorch_grad_cam.utils.image import show_cam_on_image
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
from PIL import Image

logger = logging.getLogger(__name__)

# Global model cache
_model = None
_grad_cam = None


def _get_model_and_gradcam():
    """
    Lazy load ResNet50 model and Grad-CAM wrapper.

    Returns:
        Tuple of (model, grad_cam)
    """
    global _model, _grad_cam

    if _model is None:
        logger.info("Loading ResNet50 model...")

        # Load pre-trained ResNet50
        _model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)
        _model.eval()

        # Move to GPU if available
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        _model = _model.to(device)

        # Target the final convolutional layer of ResNet50
        # ResNet50 architecture: layer4 is the final residual block
        target_layers = [_model.layer4[-1]]

        # Initialize Grad-CAM
        _grad_cam = GradCAM(model=_model, target_layers=target_layers)

        logger.info(f"ResNet50 loaded on {device}")

    return _model, _grad_cam


def _preprocess_image(image: np.ndarray) -> torch.Tensor:
    """
    Preprocess image for ResNet50 input.

    Args:
        image: BGR image from OpenCV

    Returns:
        Preprocessed tensor ready for model
    """
    # Convert BGR to RGB
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Convert to PIL Image
    pil_image = Image.fromarray(image_rgb)

    # ImageNet preprocessing
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])

    # Apply transforms and add batch dimension
    tensor = transform(pil_image).unsqueeze(0)

    return tensor


def _create_red_heatmap(
    original_image: np.ndarray,
    cam_mask: np.ndarray,
    opacity: float = 0.4
) -> np.ndarray:
    """
    Create red heatmap overlay on original image.

    Args:
        original_image: Original BGR image
        cam_mask: Grad-CAM attention mask (0-1 float values)
        opacity: Overlay opacity (0-1)

    Returns:
        Image with red heatmap overlay
    """
    # Resize CAM mask to match original image size
    cam_resized = cv2.resize(cam_mask, (original_image.shape[1], original_image.shape[0]))

    # Create red heatmap
    # High attention = bright red (255, 0, 0)
    # Low attention = transparent (0, 0, 0)
    heatmap = np.zeros_like(original_image, dtype=np.uint8)
    heatmap[:, :, 2] = (cam_resized * 255).astype(np.uint8)  # Red channel in BGR

    # Apply Gaussian blur for smooth transitions
    heatmap = cv2.GaussianBlur(heatmap, (21, 21), 0)

    # Create alpha mask based on attention strength
    alpha = cam_resized * opacity

    # Blend using alpha mask
    result = original_image.copy().astype(np.float32)
    for c in range(3):
        result[:, :, c] = result[:, :, c] * (1 - alpha) + heatmap[:, :, c] * alpha

    return result.astype(np.uint8)


def _find_salient_regions(
    cam_mask: np.ndarray,
    original_shape: tuple,
    top_n: int = 5
) -> List[Dict[str, Any]]:
    """
    Find top salient regions from Grad-CAM mask.

    Args:
        cam_mask: Grad-CAM attention mask (0-1 float values)
        original_shape: Original image shape (h, w)
        top_n: Number of top regions to return

    Returns:
        List of salient regions with bbox and scores
    """
    # Resize mask to original image dimensions
    cam_resized = cv2.resize(cam_mask, (original_shape[1], original_shape[0]))

    # Convert to 0-255 range
    cam_uint8 = (cam_resized * 255).astype(np.uint8)

    # Threshold to get high-attention areas (top 20%)
    threshold = np.percentile(cam_uint8, 80)
    _, binary_mask = cv2.threshold(cam_uint8, threshold, 255, cv2.THRESH_BINARY)

    # Apply morphological operations to clean up regions
    kernel = np.ones((5, 5), np.uint8)
    binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel)
    binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel)

    # Find contours
    contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Extract regions with scores
    regions = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = cv2.contourArea(contour)

        # Filter small regions (< 0.5% of image)
        min_area = (original_shape[0] * original_shape[1]) * 0.005
        if area < min_area:
            continue

        # Calculate mean salience score in this region
        region_mask = cam_resized[y:y+h, x:x+w]
        salience_score = float(np.mean(region_mask))

        regions.append({
            'bbox': [int(x), int(y), int(w), int(h)],
            'area': float(area),
            'salience_score': salience_score,
            'area_percentage': float(area / (original_shape[0] * original_shape[1]) * 100)
        })

    # Sort by salience score and take top N
    regions.sort(key=lambda r: r['salience_score'], reverse=True)
    return regions[:top_n]


def analyze_salience(
    rep_frame_path: str,
    job_id: str,
    output_dir: str
) -> Dict[str, Any]:
    """
    Analyze visual salience using ResNet50 + Grad-CAM to predict attention.

    Uses deep learning to predict where drivers' eyes will be naturally drawn
    based on learned visual attention patterns from ImageNet.

    Args:
        rep_frame_path: Path to representative frame from simulation
        job_id: Unique job identifier
        output_dir: Directory to save heatmap

    Returns:
        Dictionary with:
            - heatmap_url: URL to red heatmap overlay image
            - attention_score: Overall attention score (0-100)
            - top_regions: List of top salient regions with bbox and scores
    """
    logger.info(f"Analyzing visual salience with Grad-CAM for job {job_id}")

    try:
        # Load original image
        img = cv2.imread(rep_frame_path)
        if img is None:
            raise ValueError(f"Could not load image from {rep_frame_path}")

        original_shape = img.shape[:2]  # (height, width)

        # Get model and Grad-CAM
        model, grad_cam = _get_model_and_gradcam()

        # Preprocess image for model
        input_tensor = _preprocess_image(img)

        # Move to same device as model
        device = next(model.parameters()).device
        input_tensor = input_tensor.to(device)

        # Run model to get predicted class
        with torch.no_grad():
            output = model(input_tensor)
            predicted_class = output.argmax(dim=1).item()

        logger.info(f"Predicted ImageNet class: {predicted_class}")

        # Generate Grad-CAM heatmap
        # Target the predicted class for maximum activation
        targets = [ClassifierOutputTarget(predicted_class)]

        # Get CAM mask (values 0-1)
        cam_mask = grad_cam(input_tensor=input_tensor, targets=targets)
        cam_mask = cam_mask[0]  # Remove batch dimension

        # Calculate overall attention score
        # Based on mean activation and spatial concentration
        mean_activation = np.mean(cam_mask)
        std_activation = np.std(cam_mask)
        max_activation = np.max(cam_mask)

        # Attention score: combines mean (overall interest) and std (focus concentration)
        attention_score = min(100.0, (mean_activation * 40 + std_activation * 30 + max_activation * 30))

        logger.info(f"Attention score: {attention_score:.2f}")

        # Create red heatmap overlay
        heatmap_overlay = _create_red_heatmap(img, cam_mask, opacity=0.4)

        # Save heatmap
        heatmap_path = Path(output_dir) / f"{job_id}_heatmap.png"
        cv2.imwrite(str(heatmap_path), heatmap_overlay)
        logger.info(f"Saved heatmap to {heatmap_path}")

        # Find top salient regions
        top_regions = _find_salient_regions(cam_mask, original_shape, top_n=5)

        logger.info(f"Found {len(top_regions)} salient regions")

        return {
            'heatmap_url': f"/files/{job_id}_heatmap.png",
            'attention_score': float(attention_score),
            'hotspot_regions': top_regions  # Keep same key name for compatibility
        }

    except Exception as e:
        logger.error(f"Error during salience analysis: {str(e)}", exc_info=True)

        # Return default values on error
        return {
            'heatmap_url': '',
            'attention_score': 0.0,
            'hotspot_regions': []
        }


def clear_model_cache():
    """
    Clear the model cache to free up memory.
    Useful for testing or when switching configurations.
    """
    global _model, _grad_cam
    _model = None
    _grad_cam = None
    logger.info("Cleared model cache")
