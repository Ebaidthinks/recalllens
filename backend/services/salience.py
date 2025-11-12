"""
Visual salience and attention heatmap generation
"""
import cv2
import numpy as np
import torch
from torchvision import models, transforms
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import show_cam_on_image
from pathlib import Path
from typing import Dict


# Cache model
_model = None
_target_layers = None


def get_salience_model():
    """Lazy load salience detection model"""
    global _model, _target_layers
    if _model is None:
        # Use ResNet50 with GradCAM for salience detection
        _model = models.resnet50(pretrained=True)
        _model.eval()
        _target_layers = [_model.layer4[-1]]
    return _model, _target_layers


def analyze_salience(
    image_path: str,
    phone_distraction: str
) -> Dict:
    """
    Generate attention heatmap showing where drivers look

    Args:
        image_path: Path to image file
        phone_distraction: Distraction level (low/med/high)

    Returns:
        Dictionary with:
        - heatmap_path: Path to saved heatmap visualization
        - attention_map: 2D array of attention scores
        - focus_regions: List of high-attention bounding boxes
        - attention_score: Overall attention capture score (0-1)
    """
    # Load image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_float = np.float32(img_rgb) / 255

    # Get model
    model, target_layers = get_salience_model()

    # Prepare image for model
    preprocess = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    input_tensor = preprocess(img_rgb)
    input_tensor = input_tensor.unsqueeze(0)

    # Generate attention map using GradCAM
    with GradCAM(model=model, target_layers=target_layers) as cam:
        # Use default target (top prediction)
        grayscale_cam = cam(input_tensor=input_tensor, targets=None)
        grayscale_cam = grayscale_cam[0, :]

    # Resize attention map to original image size
    attention_map = cv2.resize(grayscale_cam, (img.shape[1], img.shape[0]))

    # Apply distraction penalty
    distraction_multiplier = {
        "low": 1.0,
        "med": 0.7,
        "high": 0.4
    }.get(phone_distraction, 1.0)
    attention_map = attention_map * distraction_multiplier

    # Create heatmap visualization
    img_resized = cv2.resize(img_float, (img.shape[1], img.shape[0]))
    heatmap_vis = show_cam_on_image(img_resized, attention_map, use_rgb=True)

    # Save heatmap
    heatmap_path = str(Path(image_path).parent / f"heatmap_{Path(image_path).name}")
    cv2.imwrite(heatmap_path, cv2.cvtColor(heatmap_vis, cv2.COLOR_RGB2BGR))

    # Find focus regions (areas with attention > 0.6)
    threshold = 0.6
    focus_mask = (attention_map > threshold).astype(np.uint8) * 255
    contours, _ = cv2.findContours(focus_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    focus_regions = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w * h > 100:  # Filter out tiny regions
            focus_regions.append([x, y, x + w, y + h])

    # Calculate overall attention score
    attention_score = float(np.mean(attention_map))

    return {
        "heatmap_path": heatmap_path,
        "attention_map": attention_map.tolist(),
        "focus_regions": focus_regions,
        "attention_score": min(attention_score, 1.0)
    }
