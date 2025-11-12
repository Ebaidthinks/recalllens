"""
Build PDF report and video artifacts
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors
import logging

logger = logging.getLogger(__name__)


def build_artifacts(
    job_id: str,
    original_path: str,
    simulated_path: str,
    analysis_data: Dict[str, Any],
    output_dir: str
) -> Dict[str, str]:
    """
    Build PDF report and comparison video.

    Args:
        job_id: Unique job identifier
        original_path: Path to original image
        simulated_path: Path to simulated image
        analysis_data: Complete analysis results
        output_dir: Output directory

    Returns:
        Dictionary with URLs to generated artifacts
    """
    logger.info(f"Building artifacts for job {job_id}")

    artifacts = {}

    # Generate PDF report
    try:
        pdf_path = _generate_pdf_report(
            job_id, original_path, simulated_path,
            analysis_data, output_dir
        )
        artifacts['pdf_report'] = f"/files/{Path(pdf_path).name}"
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        artifacts['pdf_report'] = None

    # Generate comparison video
    try:
        video_path = _generate_comparison_video(
            job_id, original_path, simulated_path, output_dir
        )
        artifacts['comparison_video'] = f"/files/{Path(video_path).name}"
    except Exception as e:
        logger.error(f"Error generating video: {str(e)}")
        artifacts['comparison_video'] = None

    # Add direct image links
    artifacts['original_image'] = f"/files/{Path(original_path).name}"
    artifacts['simulated_image'] = f"/files/{Path(simulated_path).name}"

    logger.info("Artifacts generation complete")
    return artifacts


def _generate_pdf_report(
    job_id: str,
    original_path: str,
    simulated_path: str,
    analysis_data: Dict[str, Any],
    output_dir: str
) -> str:
    """Generate PDF report with analysis results"""

    pdf_path = Path(output_dir) / f"{job_id}_report.pdf"
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)

    story = []
    styles = getSampleStyleSheet()

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    story.append(Paragraph("RecallLens Analysis Report", title_style))
    story.append(Spacer(1, 0.3 * inch))

    # Recall Score (Big and prominent)
    recall_score = analysis_data['recall_data']['recall_score']
    score_style = ParagraphStyle(
        'Score',
        parent=styles['Normal'],
        fontSize=48,
        textColor=colors.HexColor('#2196F3'),
        alignment=TA_CENTER,
        spaceAfter=10
    )
    story.append(Paragraph(f"<b>{recall_score:.1f}/100</b>", score_style))
    story.append(Paragraph("<b>Recall Score</b>", styles['Heading2']))
    story.append(Spacer(1, 0.3 * inch))

    # Predicted Gist
    gist = analysis_data['recall_data']['predicted_gist']
    story.append(Paragraph("<b>Predicted Driver Memory:</b>", styles['Heading3']))
    story.append(Paragraph(gist, styles['Normal']))
    story.append(Spacer(1, 0.3 * inch))

    # Environment Parameters
    env = analysis_data['env_params']
    story.append(Paragraph("<b>Test Conditions:</b>", styles['Heading3']))
    conditions_data = [
        ['Speed', f"{env['speed_kmh']} km/h"],
        ['View Distance', f"{env['view_distance_m']} meters"],
        ['Dwell Time', f"{env['dwell_sec']} seconds"],
        ['Lighting', env['lighting'].capitalize()],
        ['Distraction Level', env['phone_distraction'].upper()]
    ]
    conditions_table = Table(conditions_data, colWidths=[2 * inch, 2 * inch])
    conditions_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f5f5f5')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    story.append(conditions_table)
    story.append(Spacer(1, 0.3 * inch))

    # Images comparison
    story.append(Paragraph("<b>Visual Comparison:</b>", styles['Heading3']))

    # Try to add images (scale them down)
    try:
        img_width = 4 * inch
        story.append(Paragraph("<b>Original:</b>", styles['Normal']))
        story.append(RLImage(original_path, width=img_width, height=img_width * 0.6))
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("<b>Driver's View (Simulated):</b>", styles['Normal']))
        story.append(RLImage(simulated_path, width=img_width, height=img_width * 0.6))
    except Exception as e:
        logger.warning(f"Could not add images to PDF: {str(e)}")
        story.append(Paragraph("Images available separately", styles['Normal']))

    story.append(Spacer(1, 0.3 * inch))

    # Suggestions
    story.append(Paragraph("<b>Improvement Suggestions:</b>", styles['Heading3']))
    for i, suggestion in enumerate(analysis_data['suggestions'][:5], 1):
        priority_color = {
            'critical': '#d32f2f',
            'high': '#f57c00',
            'medium': '#fbc02d',
            'low': '#388e3c'
        }.get(suggestion['priority'], '#000000')

        story.append(Paragraph(
            f"<b>{i}. [{suggestion['priority'].upper()}] {suggestion['category']}</b>",
            ParagraphStyle('SuggestionTitle', parent=styles['Normal'], textColor=colors.HexColor(priority_color))
        ))
        story.append(Paragraph(suggestion['description'], styles['Normal']))
        story.append(Paragraph(f"<i>Expected Impact: {suggestion['impact_estimate']}</i>", styles['Normal']))
        story.append(Spacer(1, 0.15 * inch))

    # Build PDF
    doc.build(story)
    logger.info(f"PDF report generated: {pdf_path}")

    return str(pdf_path)


def _generate_comparison_video(
    job_id: str,
    original_path: str,
    simulated_path: str,
    output_dir: str,
    duration: int = 3,
    fps: int = 30
) -> str:
    """Generate side-by-side comparison video"""

    video_path = Path(output_dir) / f"{job_id}_comparison.mp4"

    # Load images
    img1 = cv2.imread(original_path)
    img2 = cv2.imread(simulated_path)

    if img1 is None or img2 is None:
        raise ValueError("Could not load images for video generation")

    # Resize to same height
    h = min(img1.shape[0], img2.shape[0])
    img1_resized = cv2.resize(img1, (int(img1.shape[1] * h / img1.shape[0]), h))
    img2_resized = cv2.resize(img2, (int(img2.shape[1] * h / img2.shape[0]), h))

    # Create side-by-side comparison
    comparison = np.hstack([img1_resized, img2_resized])

    # Add labels
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(comparison, "Original", (50, 50), font, 1.5, (255, 255, 255), 3, cv2.LINE_AA)
    cv2.putText(comparison, "Driver's View", (img1_resized.shape[1] + 50, 50), font, 1.5, (255, 255, 255), 3, cv2.LINE_AA)

    # Setup video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(
        str(video_path),
        fourcc,
        fps,
        (comparison.shape[1], comparison.shape[0])
    )

    # Write frames
    total_frames = duration * fps
    for _ in range(total_frames):
        out.write(comparison)

    out.release()

    logger.info(f"Comparison video generated: {video_path}")
    return str(video_path)
