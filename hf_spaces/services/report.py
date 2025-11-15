"""
Build professional PDF reports and video artifacts

Generates comprehensive 4-page PDF reports with executive summaries,
legibility analysis, attention heatmaps, and actionable recommendations.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage,
    Table, TableStyle, PageBreak, Frame, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.pdfgen import canvas
import logging

logger = logging.getLogger(__name__)


def build_artifacts(
    job_id: str,
    sim_result: Dict[str, Any],
    sal_result: Dict[str, Any],
    ocr_result: Dict[str, Any],
    recall_dict: Dict[str, Any],
    suggestions: List[Dict[str, str]],
    output_dir: str
) -> Dict[str, str]:
    """
    Build comprehensive PDF report and video artifacts.

    Args:
        job_id: Unique job identifier
        sim_result: Simulation results with frames, video_path, representative_frame_path
        sal_result: Salience results with heatmap_url, attention_score, hotspot_regions
        ocr_result: OCR results with words_detected, logo_visible
        recall_dict: Recall analysis with score, memory_summary, components
        suggestions: List of improvement suggestions
        output_dir: Output directory

    Returns:
        Dictionary with URLs to:
            - simulation_video: MP4 of simulation
            - heatmap_png: Attention heatmap image
            - pdf_report: Complete PDF report
    """
    logger.info(f"Building artifacts for job {job_id}")

    artifacts = {}

    # Artifact 1: Simulation video (from sim_result)
    if sim_result.get('video_path'):
        artifacts['simulation_video'] = f"/files/{Path(sim_result['video_path']).name}"
    else:
        artifacts['simulation_video'] = None

    # Artifact 2: Heatmap PNG (from sal_result)
    if sal_result.get('heatmap_url'):
        artifacts['heatmap_png'] = sal_result['heatmap_url']
    else:
        artifacts['heatmap_png'] = None

    # Artifact 3: Generate professional PDF report
    try:
        pdf_path = _generate_professional_pdf(
            job_id=job_id,
            sim_result=sim_result,
            sal_result=sal_result,
            ocr_result=ocr_result,
            recall_dict=recall_dict,
            suggestions=suggestions,
            output_dir=output_dir
        )
        artifacts['pdf_report'] = f"/files/{Path(pdf_path).name}"
        logger.info(f"PDF report generated: {pdf_path}")
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}", exc_info=True)
        artifacts['pdf_report'] = None

    logger.info("Artifacts generation complete")
    return artifacts


def _generate_professional_pdf(
    job_id: str,
    sim_result: Dict[str, Any],
    sal_result: Dict[str, Any],
    ocr_result: Dict[str, Any],
    recall_dict: Dict[str, Any],
    suggestions: List[Dict[str, str]],
    output_dir: str
) -> str:
    """
    Generate professional 4-page PDF report.

    Pages:
        1. Executive Summary
        2. Legibility Analysis
        3. Attention Heatmap
        4. Recommendations
    """
    pdf_path = Path(output_dir) / f"{job_id}_report.pdf"
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch,
        leftMargin=0.75*inch,
        rightMargin=0.75*inch
    )

    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'RecallLensTitle',
        parent=styles['Heading1'],
        fontSize=32,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    # =========================================================================
    # PAGE 1 - EXECUTIVE SUMMARY
    # =========================================================================
    logger.info("Generating Page 1: Executive Summary")

    # RecallLens Logo/Title
    story.append(Paragraph("RecallLens", title_style))
    story.append(Paragraph(
        "Billboard Recall Analysis Report",
        ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=14,
                      alignment=TA_CENTER, textColor=colors.grey, spaceAfter=30)
    ))

    # Overall Recall Score (LARGE and PROMINENT)
    recall_score = recall_dict.get('score', 0)

    # Traffic light indicator logic
    if recall_score >= 75:
        score_color = '#4CAF50'  # Green
        status_text = "EXCELLENT"
    elif recall_score >= 55:
        score_color = '#FFC107'  # Yellow/Amber
        status_text = "MODERATE"
    else:
        score_color = '#F44336'  # Red
        status_text = "POOR"

    score_style = ParagraphStyle(
        'ScoreStyle',
        parent=styles['Normal'],
        fontSize=72,
        textColor=colors.HexColor(score_color),
        alignment=TA_CENTER,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    )

    story.append(Paragraph(f"{recall_score:.1f}", score_style))
    story.append(Paragraph(
        f"<b>{status_text} RECALL PROBABILITY</b>",
        ParagraphStyle('Status', parent=styles['Normal'], fontSize=16,
                      alignment=TA_CENTER, spaceAfter=30)
    ))

    # Predicted Gist (what drivers will remember)
    predicted_gist = recall_dict.get('memory_summary', {}).get('predicted_gist', 'Unknown')
    story.append(Paragraph("<b>Predicted Driver Memory:</b>", styles['Heading3']))
    story.append(Paragraph(
        f'<i>"{predicted_gist}"</i>',
        ParagraphStyle('Gist', parent=styles['Normal'], fontSize=14,
                      spaceAfter=20, textColor=colors.HexColor('#424242'))
    ))

    # Viewing Simulation Thumbnail
    story.append(Paragraph("<b>Simulated Driver View:</b>", styles['Heading3']))
    try:
        sim_image_path = sim_result.get('representative_frame_path')
        if sim_image_path and Path(sim_image_path).exists():
            img_width = 5 * inch
            story.append(RLImage(sim_image_path, width=img_width, height=img_width * 0.6))
            story.append(Spacer(1, 0.2 * inch))
    except Exception as e:
        logger.warning(f"Could not add simulation thumbnail: {str(e)}")
        story.append(Paragraph("Simulation image not available", styles['Normal']))

    # Traffic Light Summary Table
    story.append(Paragraph("<b>Performance Summary:</b>", styles['Heading3']))
    summary_data = [
        ['Metric', 'Value', 'Status'],
        ['Recall Score', f"{recall_score:.1f}/100", status_text],
        ['Attention Score', f"{sal_result.get('attention_score', 0):.1f}/100",
         'Good' if sal_result.get('attention_score', 0) >= 60 else 'Needs Improvement'],
        ['Legible Words', f"{len([w for w in ocr_result.get('words_detected', []) if w.get('legible', False)])}/{len(ocr_result.get('words_detected', []))}",
         'Good' if len([w for w in ocr_result.get('words_detected', []) if w.get('legible', False)]) >= len(ocr_result.get('words_detected', [])) * 0.7 else 'Needs Improvement']
    ]

    summary_table = Table(summary_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')])
    ]))
    story.append(summary_table)

    # Page break to Page 2
    story.append(PageBreak())

    # =========================================================================
    # PAGE 2 - LEGIBILITY ANALYSIS
    # =========================================================================
    logger.info("Generating Page 2: Legibility Analysis")

    story.append(Paragraph("Legibility Analysis", styles['Heading1']))
    story.append(Spacer(1, 0.2 * inch))

    words_detected = ocr_result.get('words_detected', [])

    if words_detected:
        # Table of detected words
        story.append(Paragraph("<b>Detected Text Elements:</b>", styles['Heading3']))

        word_table_data = [['#', 'Text', 'Confidence', 'Height (px)', 'Legible']]

        for i, word in enumerate(words_detected[:10], 1):  # Limit to 10 words
            legible_marker = '✓' if word.get('legible', False) else '✗'
            word_table_data.append([
                str(i),
                word.get('text', '')[:30],  # Truncate long text
                f"{word.get('confidence', 0):.2f}",
                str(word.get('height_px', 0)),
                legible_marker
            ])

        word_table = Table(word_table_data, colWidths=[0.5*inch, 2.5*inch, 1*inch, 1*inch, 0.8*inch])
        word_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')])
        ]))
        story.append(word_table)
        story.append(Spacer(1, 0.3 * inch))
    else:
        story.append(Paragraph(
            "⚠ No text elements detected in the billboard.",
            ParagraphStyle('Warning', parent=styles['Normal'], textColor=colors.HexColor('#F44336'))
        ))
        story.append(Spacer(1, 0.2 * inch))

    # Minimum Readable Size Calculations
    story.append(Paragraph("<b>Readability Thresholds:</b>", styles['Heading3']))

    threshold_data = [
        ['Metric', 'Requirement', 'Analysis'],
        ['Minimum Text Height', '≥22 pixels', f"{sum(1 for w in words_detected if w.get('height_px', 0) >= 22)}/{len(words_detected)} words meet threshold"],
        ['Minimum Confidence', '≥0.70', f"{sum(1 for w in words_detected if w.get('confidence', 0) >= 0.7)}/{len(words_detected)} words meet threshold"],
        ['Recommended Word Count', '≤5 words', f"{len(words_detected)} words detected"]
    ]

    threshold_table = Table(threshold_data, colWidths=[2*inch, 1.5*inch, 2.5*inch])
    threshold_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')])
    ]))
    story.append(threshold_table)
    story.append(Spacer(1, 0.2 * inch))

    # Contrast Ratios (Placeholder)
    story.append(Paragraph("<b>Contrast Analysis:</b>", styles['Heading3']))
    story.append(Paragraph(
        "Contrast ratio analysis: <i>Coming soon</i>",
        styles['Normal']
    ))
    story.append(Paragraph(
        "Recommendation: Use complementary colors with luminance difference ≥50% for optimal readability.",
        styles['Normal']
    ))

    # Page break to Page 3
    story.append(PageBreak())

    # =========================================================================
    # PAGE 3 - ATTENTION HEATMAP
    # =========================================================================
    logger.info("Generating Page 3: Attention Heatmap")

    story.append(Paragraph("Visual Attention Analysis", styles['Heading1']))
    story.append(Spacer(1, 0.2 * inch))

    # Embed heatmap image
    story.append(Paragraph("<b>Attention Heatmap:</b>", styles['Heading3']))
    story.append(Paragraph(
        "Red areas indicate where drivers' eyes are most likely to be drawn (based on Grad-CAM deep learning analysis).",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.1 * inch))

    try:
        # Extract heatmap path from URL
        heatmap_url = sal_result.get('heatmap_url', '')
        if heatmap_url:
            heatmap_path = Path(output_dir) / heatmap_url.split('/')[-1]
            if heatmap_path.exists():
                img_width = 5.5 * inch
                story.append(RLImage(str(heatmap_path), width=img_width, height=img_width * 0.6))
                story.append(Spacer(1, 0.3 * inch))
    except Exception as e:
        logger.warning(f"Could not add heatmap image: {str(e)}")
        story.append(Paragraph("Heatmap image not available", styles['Normal']))

    # Explain salient regions
    story.append(Paragraph("<b>Top Salient Regions:</b>", styles['Heading3']))
    hotspot_regions = sal_result.get('hotspot_regions', [])

    if hotspot_regions:
        region_data = [['Rank', 'Location (x, y)', 'Size (w×h)', 'Salience Score']]

        for i, region in enumerate(hotspot_regions[:5], 1):
            bbox = region.get('bbox', [0, 0, 0, 0])
            salience_score = region.get('salience_score', 0)
            region_data.append([
                str(i),
                f"({bbox[0]}, {bbox[1]})",
                f"{bbox[2]}×{bbox[3]}",
                f"{salience_score:.3f}"
            ])

        region_table = Table(region_data, colWidths=[0.8*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        region_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')])
        ]))
        story.append(region_table)
    else:
        story.append(Paragraph("No significant salient regions detected.", styles['Normal']))

    story.append(Spacer(1, 0.2 * inch))

    # Compare to brand hierarchy
    story.append(Paragraph("<b>Brand Hierarchy Alignment:</b>", styles['Heading3']))
    story.append(Paragraph(
        "Ensure your brand logo and key message align with the high-attention zones (red areas in heatmap). "
        "Visual power zones are typically in the lower-right or upper-left quadrants.",
        styles['Normal']
    ))

    # Page break to Page 4
    story.append(PageBreak())

    # =========================================================================
    # PAGE 4 - RECOMMENDATIONS
    # =========================================================================
    logger.info("Generating Page 4: Recommendations")

    story.append(Paragraph("Actionable Recommendations", styles['Heading1']))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph(
        "Implement these changes to improve billboard recall and effectiveness:",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.2 * inch))

    # List suggestions with priority flags
    for i, suggestion in enumerate(suggestions, 1):
        # Priority badge
        suggestion_type = suggestion.get('type', 'general')
        type_colors = {
            'copy': '#2196F3',
            'contrast': '#F44336',
            'layout': '#4CAF50'
        }
        badge_color = type_colors.get(suggestion_type, '#9E9E9E')

        # Title with badge
        title_para = Paragraph(
            f"<b>{i}. [{suggestion_type.upper()}] {suggestion.get('message', '')[:60]}...</b>",
            ParagraphStyle(
                'SuggestionTitle',
                parent=styles['Normal'],
                fontSize=11,
                textColor=colors.HexColor(badge_color),
                spaceAfter=5,
                fontName='Helvetica-Bold'
            )
        )
        story.append(title_para)

        # Full message
        story.append(Paragraph(
            suggestion.get('message', ''),
            ParagraphStyle('SuggestionBody', parent=styles['Normal'], fontSize=10, leftIndent=20)
        ))

        # Impact estimate
        story.append(Paragraph(
            f"<i>{suggestion.get('estimated_impact', 'Impact unknown')}</i>",
            ParagraphStyle('Impact', parent=styles['Normal'], fontSize=9,
                          textColor=colors.grey, leftIndent=20, spaceAfter=15)
        ))

    # Estimated Score Improvements Summary
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("<b>Expected Results:</b>", styles['Heading3']))

    # Calculate total potential improvement
    total_improvement = 0
    for suggestion in suggestions:
        impact_str = suggestion.get('estimated_impact', '')
        import re
        match = re.search(r'~(\d+)%', impact_str)
        if match:
            total_improvement += int(match.group(1))

    projected_score = min(100, recall_score + total_improvement)

    results_data = [
        ['Metric', 'Current', 'Projected (After Improvements)'],
        ['Recall Score', f"{recall_score:.1f}/100", f"{projected_score:.1f}/100"],
        ['Estimated Improvement', '-', f"+{total_improvement}%"]
    ]

    results_table = Table(results_data, colWidths=[2*inch, 2*inch, 2*inch])
    results_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')])
    ]))
    story.append(results_table)

    # Before/After placeholder
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("<b>Before/After Comparison:</b>", styles['Heading3']))
    story.append(Paragraph(
        "<i>Visual mockups available upon request. Contact your RecallLens representative for redesign services.</i>",
        styles['Normal']
    ))

    # Build PDF
    doc.build(story)
    logger.info(f"Professional PDF report generated: {pdf_path}")

    return str(pdf_path)
