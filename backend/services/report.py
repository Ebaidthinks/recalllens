"""
Generate PDF reports and video artifacts
"""
import cv2
import numpy as np
from pathlib import Path
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from typing import Dict, List
import ffmpeg


def build_artifacts(
    job_id: str,
    original_path: str,
    simulated_path: str,
    heatmap_path: str,
    recall_data: Dict,
    text_data: Dict,
    salience_data: Dict,
    suggestions: List[Dict],
    params: Dict
) -> Dict:
    """
    Generate PDF report and comparison video

    Args:
        job_id: Unique job identifier
        original_path: Path to original image
        simulated_path: Path to simulated view
        heatmap_path: Path to attention heatmap
        recall_data: Memory analysis results
        text_data: OCR results
        salience_data: Attention analysis results
        suggestions: List of improvement suggestions
        params: Original request parameters

    Returns:
        Dictionary with:
        - pdf_path: Path to generated PDF report
        - video_path: Path to comparison video
    """
    output_dir = Path(original_path).parent
    pdf_path = str(output_dir / f"report_{job_id}.pdf")
    video_path = str(output_dir / f"comparison_{job_id}.mp4")

    # Generate PDF report
    _generate_pdf_report(
        pdf_path,
        original_path,
        simulated_path,
        heatmap_path,
        recall_data,
        text_data,
        salience_data,
        suggestions,
        params
    )

    # Generate comparison video
    _generate_comparison_video(
        video_path,
        original_path,
        simulated_path,
        heatmap_path,
        params["dwell_sec"]
    )

    return {
        "pdf_path": pdf_path,
        "video_path": video_path
    }


def _generate_pdf_report(
    pdf_path: str,
    original_path: str,
    simulated_path: str,
    heatmap_path: str,
    recall_data: Dict,
    text_data: Dict,
    salience_data: Dict,
    suggestions: List[Dict],
    params: Dict
):
    """Generate detailed PDF report"""
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    story.append(Paragraph("RecallLens Analysis Report", title_style))
    story.append(Spacer(1, 0.3 * inch))

    # Summary Section
    story.append(Paragraph("Executive Summary", styles['Heading2']))
    story.append(Spacer(1, 0.2 * inch))

    summary_data = [
        ["Metric", "Score", "Rating"],
        ["Recall Probability", f"{recall_data['recall_score']:.1%}",
         _get_rating(recall_data['recall_score'])],
        ["Text Legibility", f"{text_data['legibility_score']:.1%}",
         _get_rating(text_data['legibility_score'])],
        ["Visual Attention", f"{salience_data['attention_score']:.1%}",
         _get_rating(salience_data['attention_score'])],
        ["Cognitive Load", f"{recall_data['cognitive_load']:.1%}",
         _get_rating(1.0 - recall_data['cognitive_load'])],
    ]

    summary_table = Table(summary_data, colWidths=[2.5 * inch, 1.5 * inch, 1.5 * inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.3 * inch))

    # Test Parameters
    story.append(Paragraph("Test Parameters", styles['Heading2']))
    story.append(Spacer(1, 0.1 * inch))

    param_text = f"""
    <b>Speed:</b> {params['speed_kmh']} km/h<br/>
    <b>Viewing Distance:</b> {params['view_distance_m']} meters<br/>
    <b>Dwell Time:</b> {params['dwell_sec']} seconds<br/>
    <b>Lighting:</b> {params['lighting']}<br/>
    <b>Phone Distraction:</b> {params['phone_distraction']}
    """
    story.append(Paragraph(param_text, styles['Normal']))
    story.append(Spacer(1, 0.3 * inch))

    # Predicted Recall
    story.append(Paragraph("Predicted Recall", styles['Heading2']))
    story.append(Spacer(1, 0.1 * inch))
    gist_text = f"<i>Viewers will likely remember: <b>{recall_data['predicted_gist']}</b></i>"
    story.append(Paragraph(gist_text, styles['Normal']))
    story.append(Spacer(1, 0.3 * inch))

    # Images
    story.append(PageBreak())
    story.append(Paragraph("Visual Comparison", styles['Heading2']))
    story.append(Spacer(1, 0.2 * inch))

    # Add images side by side
    for title, img_path in [("Original", original_path),
                             ("Simulated View", simulated_path),
                             ("Attention Heatmap", heatmap_path)]:
        story.append(Paragraph(title, styles['Heading3']))
        story.append(Spacer(1, 0.1 * inch))
        img = Image(img_path, width=5 * inch, height=3 * inch)
        story.append(img)
        story.append(Spacer(1, 0.2 * inch))

    # Suggestions
    story.append(PageBreak())
    story.append(Paragraph("Improvement Suggestions", styles['Heading2']))
    story.append(Spacer(1, 0.2 * inch))

    for i, sug in enumerate(suggestions, 1):
        severity_color = {
            "high": colors.red,
            "medium": colors.orange,
            "low": colors.green
        }.get(sug['severity'], colors.grey)

        sug_title = f"{i}. [{sug['severity'].upper()}] {sug['issue']}"
        story.append(Paragraph(sug_title, styles['Heading4']))
        story.append(Spacer(1, 0.05 * inch))

        fix_text = f"<b>Fix:</b> {sug['fix']}<br/><b>Expected Impact:</b> {sug['impact']}"
        story.append(Paragraph(fix_text, styles['Normal']))
        story.append(Spacer(1, 0.15 * inch))

    # Build PDF
    doc.build(story)


def _generate_comparison_video(
    video_path: str,
    original_path: str,
    simulated_path: str,
    heatmap_path: str,
    dwell_sec: float
):
    """Generate side-by-side comparison video"""
    # Load images
    original = cv2.imread(original_path)
    simulated = cv2.imread(simulated_path)
    heatmap = cv2.imread(heatmap_path)

    if original is None or simulated is None or heatmap is None:
        raise ValueError("Could not load one or more images for video generation")

    # Resize all to same height
    target_height = 480
    original = _resize_to_height(original, target_height)
    simulated = _resize_to_height(simulated, target_height)
    heatmap = _resize_to_height(heatmap, target_height)

    # Create side-by-side comparison
    comparison = np.hstack([original, simulated, heatmap])

    # Add labels
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(comparison, "Original", (10, 30), font, 1, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(comparison, "Driver View", (original.shape[1] + 10, 30), font, 1, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(comparison, "Attention", (original.shape[1] + simulated.shape[1] + 10, 30), font, 1, (255, 255, 255), 2, cv2.LINE_AA)

    # Write video (hold for dwell_sec * 2)
    fps = 30
    duration = int(dwell_sec * 2)  # Show comparison for twice the dwell time
    frames = fps * duration

    height, width = comparison.shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_path, fourcc, fps, (width, height))

    for _ in range(frames):
        out.write(comparison)

    out.release()


def _resize_to_height(img, target_height):
    """Resize image to target height maintaining aspect ratio"""
    h, w = img.shape[:2]
    aspect_ratio = w / h
    target_width = int(target_height * aspect_ratio)
    return cv2.resize(img, (target_width, target_height))


def _get_rating(score: float) -> str:
    """Convert score to rating"""
    if score >= 0.8:
        return "Excellent"
    elif score >= 0.6:
        return "Good"
    elif score >= 0.4:
        return "Fair"
    elif score >= 0.2:
        return "Poor"
    else:
        return "Very Poor"
