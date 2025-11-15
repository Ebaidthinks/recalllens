"""
RecallLens - Billboard Recall Prediction System
Gradio Interface for Hugging Face Spaces
"""

import gradio as gr
import os
import sys
import time
from pathlib import Path
from PIL import Image
import logging
import hashlib

# Add services to path
sys.path.insert(0, str(Path(__file__).parent))

# Import pipeline services
from services.simulate import simulate_view, list_dubai_presets
from services.ocr import extract_text_tokens_from_path
from services.salience import analyze_salience
from services.memory import compute_recall
from services.suggest import make_suggestions
from services.report import build_artifacts

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create necessary directories
UPLOAD_DIR = Path("assets/uploads")
OUTPUT_DIR = Path("assets/outputs")
SAMPLES_DIR = Path("assets/samples")

for dir_path in [UPLOAD_DIR, OUTPUT_DIR, SAMPLES_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Dubai road presets
DUBAI_PRESETS = {
    "Custom Settings": None,
    "Sheikh Zayed Road (SZR) - 120 km/h": {
        "speed_kmh": 120.0,
        "view_distance_m": 40.0,
        "dwell_sec": 0.8,
        "lighting": "dubai_day",
        "phone_distraction": "med"
    },
    "Al Khail Road - 100 km/h": {
        "speed_kmh": 100.0,
        "view_distance_m": 35.0,
        "dwell_sec": 1.0,
        "lighting": "dubai_day",
        "phone_distraction": "med"
    },
    "JBR Beach Road - 60 km/h": {
        "speed_kmh": 60.0,
        "view_distance_m": 25.0,
        "dwell_sec": 1.5,
        "lighting": "day",
        "phone_distraction": "low"
    },
    "Dubai Marina - 40 km/h": {
        "speed_kmh": 40.0,
        "view_distance_m": 20.0,
        "dwell_sec": 2.0,
        "lighting": "night",
        "phone_distraction": "low"
    }
}


def analyze_billboard(
    image,
    preset,
    speed_kmh,
    view_distance_m,
    dwell_sec,
    lighting,
    phone_distraction
):
    """
    Main analysis function that processes the billboard through the full pipeline.
    """
    try:
        logger.info("Starting billboard analysis...")
        start_time = time.time()

        # Validate image
        if image is None:
            return None, None, None, "❌ Please upload a billboard image", "", "", None

        # Apply preset if selected
        if preset != "Custom Settings":
            preset_params = DUBAI_PRESETS[preset]
            speed_kmh = preset_params["speed_kmh"]
            view_distance_m = preset_params["view_distance_m"]
            dwell_sec = preset_params["dwell_sec"]
            lighting = preset_params["lighting"]
            phone_distraction = preset_params["phone_distraction"]

        # Generate unique job ID
        job_id = hashlib.md5(f"{time.time()}_{speed_kmh}".encode()).hexdigest()[:12]
        input_path = UPLOAD_DIR / f"{job_id}_input.jpg"

        # Save uploaded image
        if isinstance(image, str):
            img = Image.open(image)
        else:
            img = image

        img.save(input_path, "JPEG", quality=95)
        logger.info(f"Saved input image: {input_path}")

        # Create environment parameters
        env_params = {
            "speed_kmh": float(speed_kmh),
            "view_distance_m": float(view_distance_m),
            "dwell_sec": float(dwell_sec),
            "lighting": lighting,
            "phone_distraction": phone_distraction
        }

        logger.info(f"Environment params: {env_params}")

        # Step 1: Simulate viewing conditions
        logger.info("Step 1/5: Simulating viewing conditions...")
        sim_result = simulate_view(
            input_path=str(input_path),
            env_dict=env_params,
            job_id=job_id,
            output_dir=str(OUTPUT_DIR)
        )
        simulated_img_path = Path(sim_result["simulated_path"])
        simulated_video_path = Path(sim_result.get("video_path", "")) if sim_result.get("video_path") else None

        # Step 2: Extract text via OCR
        logger.info("Step 2/5: Extracting text with OCR...")
        ocr_result = extract_text_tokens_from_path(str(simulated_img_path))

        # Step 3: Compute salience/attention
        logger.info("Step 3/5: Computing visual attention...")
        salience_result = analyze_salience(
            simulated_img=str(simulated_img_path),
            job_id=job_id,
            output_dir=str(OUTPUT_DIR)
        )
        heatmap_path = Path(salience_result["heatmap_overlay_path"])

        # Step 4: Predict memory recall
        logger.info("Step 4/5: Predicting memory recall...")
        memory_result = compute_recall(
            env_dict=env_params,
            ocr_result=ocr_result,
            sal_result=salience_result
        )

        # Step 5: Generate suggestions
        logger.info("Step 5/5: Generating optimization suggestions...")
        suggestions_list = make_suggestions(
            recall_dict=memory_result,
            ocr_result=ocr_result,
            sal_result=salience_result
        )

        # Generate PDF report
        logger.info("Generating PDF report...")
        artifacts_result = build_artifacts(
            job_id=job_id,
            sim_result=sim_result,
            sal_result=salience_result,
            ocr_result=ocr_result,
            recall_dict=memory_result,
            suggestions_list=suggestions_list,
            output_dir=str(OUTPUT_DIR)
        )
        pdf_path = artifacts_result["pdf_path"]

        # Calculate total time
        total_time = time.time() - start_time

        # Prepare results
        recall_score = memory_result["recall_score"]
        recall_rating = memory_result.get("rating", "Unknown")

        # Format extracted text
        text_blocks = ocr_result.get("text_blocks", [])
        extracted_text = "### Extracted Text\n\n"
        if text_blocks:
            for i, block in enumerate(text_blocks[:10], 1):  # Show top 10
                extracted_text += f"{i}. **{block['text']}** (confidence: {block['confidence']:.0%})\n"
        else:
            extracted_text += "*No text detected*\n"

        # Format language info
        lang_info = ocr_result.get("language_analysis", {})
        if lang_info:
            extracted_text += f"\n### Language Analysis\n\n"
            extracted_text += f"- **Arabic:** {lang_info.get('arabic_percentage', 0):.1f}%\n"
            extracted_text += f"- **English:** {lang_info.get('english_percentage', 0):.1f}%\n"
            extracted_text += f"- **Direction:** {lang_info.get('direction', 'ltr').upper()}\n"
            extracted_text += f"- **Mix:** {lang_info.get('language_mix', 'unknown')}\n"

        # Format suggestions
        suggestions_text = "### Optimization Suggestions\n\n"
        if suggestions_list:
            for i, sugg in enumerate(suggestions_list[:5], 1):  # Top 5 suggestions
                suggestions_text += f"#### {i}. {sugg['category']} (Impact: {sugg.get('impact', 'medium')})\n\n"
                suggestions_text += f"**Recommendation:** {sugg['recommendation']}\n\n"
                suggestions_text += f"**Why:** {sugg['reason']}\n\n"
                suggestions_text += "---\n\n"
        else:
            suggestions_text += "*No optimization suggestions at this time.*\n"

        # Create status message
        status_msg = f"""
## ✅ Analysis Complete!

### Recall Score: **{recall_score:.1f}/100** ({recall_rating})

### Performance
- **Processing Time:** {total_time:.2f} seconds
- **Simulated Frames:** {sim_result.get('num_frames', 0)}
- **Text Regions:** {len(text_blocks)}
- **Salient Regions:** {salience_result.get('num_regions', 0)}

### Environment Settings
- **Speed:** {speed_kmh} km/h
- **Distance:** {view_distance_m} m
- **Dwell Time:** {dwell_sec} sec
- **Lighting:** {lighting}
- **Distraction:** {phone_distraction}
"""

        logger.info(f"Analysis complete! Recall score: {recall_score:.1f} (took {total_time:.2f}s)")

        return (
            str(simulated_img_path),  # Simulated view
            str(heatmap_path),  # Attention heatmap
            str(simulated_video_path) if simulated_video_path and simulated_video_path.exists() else None,  # Video
            status_msg,  # Status
            extracted_text,  # OCR text
            suggestions_text,  # Suggestions
            str(pdf_path)  # PDF report
        )

    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        error_msg = f"""
## ❌ Analysis Failed

**Error:** {str(e)}

**Troubleshooting:**
1. Make sure the image is a valid billboard photo
2. Try a different image format (JPG, PNG)
3. Check that the image is not corrupted
4. Try with smaller image dimensions

If the error persists, please report it with the error message above.
"""
        return None, None, None, error_msg, "", "", None


def update_preset(preset_name):
    """Update sliders based on selected preset."""
    if preset_name == "Custom Settings":
        return 80.0, 30.0, 1.2, "day", "med"

    preset = DUBAI_PRESETS[preset_name]
    return (
        preset["speed_kmh"],
        preset["view_distance_m"],
        preset["dwell_sec"],
        preset["lighting"],
        preset["phone_distraction"]
    )


# Create Gradio interface
with gr.Blocks(title="RecallLens - Billboard Recall Prediction", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🎯 RecallLens - Billboard Recall Prediction

    Upload a billboard image and analyze how memorable it will be for drivers.

    **Features:**
    - 🚗 Simulate real viewing conditions (speed, distance, lighting)
    - 🧠 Predict memory recall scores (0-100)
    - 🔥 Visual attention heatmaps (ResNet50 + Grad-CAM)
    - 🌍 Dubai-specific road presets (SZR, Al Khail, JBR, Marina)
    - 🔤 Arabic + English text detection (PaddleOCR)
    - 💡 AI-generated optimization suggestions
    - 📄 Professional PDF reports
    """)

    with gr.Row():
        # Left column: Input
        with gr.Column(scale=1):
            gr.Markdown("### 📤 Upload Billboard")
            image_input = gr.Image(
                type="pil",
                label="Billboard Image",
                height=300
            )

            gr.Markdown("### ⚙️ Environment Settings")

            preset_dropdown = gr.Dropdown(
                choices=list(DUBAI_PRESETS.keys()),
                value="Custom Settings",
                label="Dubai Road Presets",
                info="Select a preset or use custom settings"
            )

            speed_slider = gr.Slider(
                minimum=20,
                maximum=140,
                value=80,
                step=5,
                label="Vehicle Speed (km/h)",
                info="How fast is the traffic?"
            )

            distance_slider = gr.Slider(
                minimum=10,
                maximum=60,
                value=30,
                step=5,
                label="Viewing Distance (meters)",
                info="How far is the billboard from the road?"
            )

            dwell_slider = gr.Slider(
                minimum=0.5,
                maximum=5.0,
                value=1.2,
                step=0.1,
                label="Dwell Time (seconds)",
                info="How long can drivers view it?"
            )

            lighting_dropdown = gr.Dropdown(
                choices=[
                    "day", "dusk", "night",
                    "dubai_day", "dubai_dusk", "dubai_night"
                ],
                value="day",
                label="Lighting Conditions",
                info="Time of day and location"
            )

            distraction_dropdown = gr.Dropdown(
                choices=["low", "med", "high"],
                value="med",
                label="Phone Distraction Level",
                info="How distracted are drivers?"
            )

            analyze_btn = gr.Button("🔍 Analyze Billboard", variant="primary", size="lg")

        # Right column: Results
        with gr.Column(scale=1):
            gr.Markdown("### 📊 Analysis Results")

            status_output = gr.Markdown("*Upload an image and click Analyze to get started.*")

            with gr.Tabs():
                with gr.Tab("🖼️ Simulated View"):
                    simulated_output = gr.Image(label="How drivers see your billboard")

                with gr.Tab("🔥 Attention Heatmap"):
                    heatmap_output = gr.Image(label="Where drivers look")

                with gr.Tab("🎬 Video Simulation"):
                    video_output = gr.Video(label="Driving simulation")

                with gr.Tab("📝 Extracted Text"):
                    text_output = gr.Markdown()

                with gr.Tab("💡 Suggestions"):
                    suggestions_output = gr.Markdown()

            pdf_output = gr.File(label="📄 Download PDF Report")

    # Wire up preset dropdown
    preset_dropdown.change(
        fn=update_preset,
        inputs=[preset_dropdown],
        outputs=[speed_slider, distance_slider, dwell_slider, lighting_dropdown, distraction_dropdown]
    )

    # Wire up analyze button
    analyze_btn.click(
        fn=analyze_billboard,
        inputs=[
            image_input,
            preset_dropdown,
            speed_slider,
            distance_slider,
            dwell_slider,
            lighting_dropdown,
            distraction_dropdown
        ],
        outputs=[
            simulated_output,
            heatmap_output,
            video_output,
            status_output,
            text_output,
            suggestions_output,
            pdf_output
        ]
    )

    gr.Markdown("""
    ---
    ### 📖 How to Use

    1. **Upload** a billboard image (portrait format works best for lamppost billboards)
    2. **Select** a Dubai road preset or customize environment settings
    3. **Click** "Analyze Billboard" (first analysis may take 30-60 seconds for model loading)
    4. **Review** the recall score, attention heatmap, extracted text, and suggestions
    5. **Download** the professional PDF report

    ### 🌟 Example Use Cases

    - **Outdoor Advertising Agencies:** Test billboard designs before printing
    - **Brand Managers:** Optimize campaign creative for maximum recall
    - **Media Buyers:** Compare billboard locations by predicted visibility
    - **Designers:** Validate text readability and visual hierarchy

    ### 🔬 Technology Stack

    - **Simulation:** OpenCV (motion blur, atmospheric effects)
    - **OCR:** PaddleOCR (Arabic + English text extraction)
    - **Attention:** ResNet50 + Grad-CAM (visual saliency heatmaps)
    - **Memory Model:** Multi-factor recall prediction (exposure, dwell, salience, readability)
    - **Reports:** ReportLab (professional PDF generation)
    - **Video:** FFmpeg (driving simulation videos)

    ### 📊 Recall Score Guide

    - **90-100:** Excellent (highly memorable)
    - **70-89:** Good (above average recall)
    - **50-69:** Fair (moderate recall)
    - **30-49:** Poor (low recall)
    - **0-29:** Very Poor (likely forgotten)

    ---

    **Built for Dubai's outdoor advertising market** 🇦🇪

    Optimized for high-speed roads, intense sunlight, and bilingual (Arabic/English) messaging.
    """)

# Launch the app
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
