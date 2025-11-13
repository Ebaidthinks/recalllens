#!/usr/bin/env python3
"""
RecallLens Pipeline Test Script

Tests the complete analysis pipeline with timing and validation.
Usage: python test_pipeline.py [image_path]
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from services.simulate import simulate_view
from services.ocr import extract_text_tokens
from services.salience import analyze_salience
from services.memory import compute_recall
from services.suggest import make_suggestions
from services.report import build_artifacts


def print_banner(text):
    """Print a formatted banner"""
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80 + "\n")


def print_step(step_num, text):
    """Print step header"""
    print(f"\n[Step {step_num}/6] {text}")
    print("-" * 60)


def validate_output(result, expected_keys, result_type):
    """Validate that output contains expected keys"""
    missing_keys = [k for k in expected_keys if k not in result]
    if missing_keys:
        print(f"  ❌ VALIDATION FAILED: Missing keys in {result_type}: {missing_keys}")
        return False
    print(f"  ✓ {result_type} structure valid")
    return True


def test_pipeline(image_path=None):
    """Run complete pipeline test"""

    print_banner("RecallLens Pipeline Test")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Setup
    base_dir = Path(__file__).parent
    assets_dir = base_dir / "assets"
    samples_dir = assets_dir / "samples"
    outputs_dir = assets_dir / "outputs"

    # Find test image
    if image_path:
        test_image = Path(image_path)
    else:
        # Look for sample images
        sample_files = list(samples_dir.glob("*.jpg")) + list(samples_dir.glob("*.png"))
        if not sample_files:
            print("❌ ERROR: No sample images found in assets/samples/")
            print(f"   Please add a sample billboard image to: {samples_dir}")
            return False
        test_image = sample_files[0]

    if not test_image.exists():
        print(f"❌ ERROR: Image not found: {test_image}")
        return False

    print(f"Test image: {test_image}")
    print(f"Output dir: {outputs_dir}\n")

    # Test parameters
    job_id = f"test_{int(time.time())}"
    env_params = {
        'speed_kmh': 100.0,
        'view_distance_m': 40.0,
        'dwell_sec': 1.0,
        'lighting': 'day',
        'phone_distraction': 'low'
    }

    print("Test parameters:")
    for key, value in env_params.items():
        print(f"  {key}: {value}")

    timings = {}
    total_start = time.time()

    try:
        # Step 1: Simulation
        print_step(1, "Simulating Driver View")
        step_start = time.time()
        simulation_result = simulate_view(
            str(test_image),
            env_params,
            job_id,
            str(outputs_dir)
        )
        timings['simulation'] = time.time() - step_start

        print(f"  Duration: {timings['simulation']:.2f}s")
        valid = validate_output(
            simulation_result,
            ['frames', 'video_path', 'representative_frame_path'],
            "simulation_result"
        )
        if not valid:
            return False

        print(f"  - Generated {len(simulation_result['frames'])} frames")
        print(f"  - Video: {simulation_result['video_path']}")
        print(f"  - Representative frame: {simulation_result['representative_frame_path']}")

        # Step 2: OCR
        print_step(2, "Extracting Text with OCR")
        step_start = time.time()
        ocr_result = extract_text_tokens(simulation_result['frames'])
        timings['ocr'] = time.time() - step_start

        print(f"  Duration: {timings['ocr']:.2f}s")
        valid = validate_output(
            ocr_result,
            ['words_detected', 'logo_visible', 'brand_color_match'],
            "ocr_result"
        )
        if not valid:
            return False

        words = ocr_result['words_detected']
        legible_count = sum(1 for w in words if w['legible'])
        print(f"  - Found {len(words)} text elements")
        print(f"  - Legible: {legible_count}/{len(words)}")
        if words:
            print(f"  - Sample text: {words[0]['text'][:50]}")

        # Step 3: Salience Analysis
        print_step(3, "Analyzing Visual Salience")
        step_start = time.time()
        salience_data = analyze_salience(
            simulation_result['representative_frame_path'],
            job_id,
            str(outputs_dir)
        )
        timings['salience'] = time.time() - step_start

        print(f"  Duration: {timings['salience']:.2f}s")
        valid = validate_output(
            salience_data,
            ['heatmap_url', 'attention_score', 'hotspot_regions'],
            "salience_data"
        )
        if not valid:
            return False

        print(f"  - Attention score: {salience_data['attention_score']:.3f}")
        print(f"  - Found {len(salience_data['hotspot_regions'])} salient regions")
        print(f"  - Heatmap: {salience_data['heatmap_url']}")

        # Step 4: Memory Recall
        print_step(4, "Computing Memory Recall Score")
        step_start = time.time()
        recall_data = compute_recall(
            ocr_result,
            salience_data,
            simulation_result['representative_frame_path']
        )
        timings['memory'] = time.time() - step_start

        print(f"  Duration: {timings['memory']:.2f}s")
        valid = validate_output(
            recall_data,
            ['score', 'memory_summary', 'component_scores'],
            "recall_data"
        )
        if not valid:
            return False

        print(f"  - Recall score: {recall_data['score']:.1f}/100")
        print(f"  - Predicted gist: {recall_data['memory_summary']['predicted_gist'][:80]}...")

        # Step 5: Suggestions
        print_step(5, "Generating Improvement Suggestions")
        step_start = time.time()
        suggestions = make_suggestions(
            recall_data,
            ocr_result,
            salience_data
        )
        timings['suggestions'] = time.time() - step_start

        print(f"  Duration: {timings['suggestions']:.2f}s")
        print(f"  - Generated {len(suggestions)} recommendations")
        if suggestions:
            print(f"  - Top priority: {suggestions[0]['category']}")

        # Step 6: Build Artifacts
        print_step(6, "Building Artifacts (PDF Report)")
        step_start = time.time()
        artifacts = build_artifacts(
            job_id=job_id,
            sim_result=simulation_result,
            sal_result=salience_data,
            ocr_result=ocr_result,
            recall_dict=recall_data,
            suggestions=suggestions,
            output_dir=str(outputs_dir)
        )
        timings['artifacts'] = time.time() - step_start

        print(f"  Duration: {timings['artifacts']:.2f}s")
        valid = validate_output(
            artifacts,
            ['simulation_video', 'heatmap_png', 'pdf_report'],
            "artifacts"
        )
        if not valid:
            return False

        print(f"  - Simulation video: {artifacts['simulation_video']}")
        print(f"  - Heatmap PNG: {artifacts['heatmap_png']}")
        print(f"  - PDF report: {artifacts['pdf_report']}")

        # Validate files exist
        print("\nValidating generated files...")
        for key, url in artifacts.items():
            # Extract path from URL (remove /files/ prefix)
            file_path = outputs_dir / url.split('/files/')[-1]
            if file_path.exists():
                size_kb = file_path.stat().st_size / 1024
                print(f"  ✓ {key}: {size_kb:.1f} KB")
            else:
                print(f"  ❌ {key}: FILE NOT FOUND at {file_path}")
                return False

        # Summary
        total_time = time.time() - total_start
        print_banner("Test Summary")

        print("✓ All pipeline steps completed successfully\n")

        print("Timing Breakdown:")
        print("-" * 60)
        for step, duration in timings.items():
            percentage = (duration / total_time) * 100
            bar_length = int(percentage / 2)
            bar = "█" * bar_length + "░" * (50 - bar_length)
            print(f"  {step:15s} {duration:6.2f}s  {bar} {percentage:5.1f}%")

        print(f"\n  {'TOTAL':15s} {total_time:6.2f}s\n")

        print("Output Format Validation:")
        print("-" * 60)
        print("  ✓ simulation_result structure")
        print("  ✓ ocr_result structure")
        print("  ✓ salience_data structure")
        print("  ✓ recall_data structure")
        print("  ✓ suggestions structure")
        print("  ✓ artifacts structure")
        print("  ✓ All files generated\n")

        print("Key Metrics:")
        print("-" * 60)
        print(f"  Recall Score:      {recall_data['score']:.1f}/100")
        print(f"  Text Elements:     {len(words)}")
        print(f"  Legible Words:     {legible_count}")
        print(f"  Attention Score:   {salience_data['attention_score']:.3f}")
        print(f"  Recommendations:   {len(suggestions)}\n")

        print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print_banner("✓ PIPELINE TEST PASSED")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: Pipeline failed")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Get image path from command line or use default
    image_path = sys.argv[1] if len(sys.argv) > 1 else None

    success = test_pipeline(image_path)
    sys.exit(0 if success else 1)
