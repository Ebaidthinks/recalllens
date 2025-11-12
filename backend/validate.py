"""
RecallLens Validation Script

This script validates the RecallLens algorithm by:
1. Processing sample billboard images through the analysis pipeline
2. Generating predicted recall scores and gists
3. Creating validation materials for human testing
4. Outputting results in CSV format for comparison

VALIDATION STUDY PROTOCOL:
=========================

Step 1: Process Sample Billboards
---------------------------------
$ cd backend
$ python validate.py

This will:
- Process 5 sample billboards from assets/samples/
- Generate simulated driver view videos (1 second each)
- Output predictions to validation_results.csv
- Create validation_report.txt with full details

Step 2: Prepare Human Validation Study
--------------------------------------
Materials needed:
- 5 simulation videos (generated in assets/outputs/)
- Response sheet for each participant
- Quiet testing environment

Step 3: Run Human Validation (10 TMS members)
---------------------------------------------
For each participant:
1. Explain: "You'll see 5 billboards as if you're driving past them at highway speed"
2. Show each 1-second simulation video ONCE
3. After EACH video, ask: "Write down 3 things you remember"
4. Record responses immediately (before showing next video)
5. Do NOT allow rewatching

Response Sheet Format:
Billboard 1: ________________
            ________________
            ________________

Billboard 2: ________________
            ________________
            ________________
...

Step 4: Score Human Responses
-----------------------------
For each participant's responses:
1. Extract key elements (colors, words, numbers)
2. Compare to predicted_gist from CSV
3. Calculate match score:
   - Exact word match: 1 point
   - Semantic match: 0.5 points
   - Color match: 0.5 points
   - Max 3 points per billboard

Step 5: Analyze Results
----------------------
Calculate:
- Average match percentage per billboard
- Correlation between predicted_score and actual_recall
- Calibration: Do 75% scores → 75% actual recall?

Expected Results:
- Match accuracy ≥60% indicates good gist prediction
- Correlation ≥0.7 indicates good score calibration
- Use results to tune sigmoid weights in memory.py

"""

import sys
import os
from pathlib import Path
import csv
from datetime import datetime
import json
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import service modules
from services.simulate import simulate_view
from services.ocr import extract_text_tokens
from services.salience import analyze_salience
from services.memory import compute_recall
from services.suggest import make_suggestions

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_recalllens(samples_dir: str = "assets/samples", output_dir: str = "assets/outputs"):
    """
    Run validation analysis on sample billboards.

    Args:
        samples_dir: Directory containing sample billboard images
        output_dir: Directory for output files

    Returns:
        List of validation results
    """
    logger.info("=" * 80)
    logger.info("RecallLens Validation Study")
    logger.info("=" * 80)

    # Create directories if they don't exist
    samples_path = Path(samples_dir)
    output_path = Path(output_dir)
    samples_path.mkdir(parents=True, exist_ok=True)
    output_path.mkdir(parents=True, exist_ok=True)

    # Find sample images
    image_extensions = ['.jpg', '.jpeg', '.png']
    sample_images = []
    for ext in image_extensions:
        sample_images.extend(samples_path.glob(f'*{ext}'))

    if not sample_images:
        logger.error(f"No sample images found in {samples_dir}")
        logger.info("Please add billboard images to backend/assets/samples/")
        logger.info("Accepted formats: .jpg, .jpeg, .png")
        return []

    logger.info(f"Found {len(sample_images)} sample image(s)")

    # Validation parameters (simulating typical highway conditions)
    validation_params = {
        'speed_kmh': 100.0,
        'view_distance_m': 40.0,
        'dwell_sec': 1.0,  # 1 second for validation study
        'lighting': 'day',
        'phone_distraction': 'low'
    }

    results = []

    # Process each sample
    for i, image_path in enumerate(sample_images[:5], 1):  # Limit to 5 samples
        job_id = f"validation_{i:02d}"
        logger.info(f"\n{'='*80}")
        logger.info(f"Processing Sample {i}: {image_path.name}")
        logger.info(f"{'='*80}")

        try:
            # Step 1: Simulate driver view
            logger.info("Step 1: Simulating driver view (1 second)")
            sim_result = simulate_view(
                str(image_path),
                validation_params,
                job_id,
                str(output_path)
            )

            # Step 2: OCR text extraction
            logger.info("Step 2: Extracting text (OCR)")
            ocr_result = extract_text_tokens(sim_result['frames'])

            # Step 3: Visual salience analysis
            logger.info("Step 3: Analyzing visual salience")
            sal_result = analyze_salience(
                sim_result['representative_frame_path'],
                job_id,
                str(output_path)
            )

            # Step 4: Compute recall score
            logger.info("Step 4: Computing recall score")
            recall_dict = compute_recall(
                ocr_result,
                sal_result,
                sim_result['representative_frame_path']
            )

            # Step 5: Generate suggestions
            logger.info("Step 5: Generating suggestions")
            suggestions = make_suggestions(
                recall_dict,
                ocr_result,
                sal_result
            )

            # Extract results
            result = {
                'sample_id': i,
                'job_id': job_id,
                'filename': image_path.name,
                'recall_score': recall_dict['score'],
                'predicted_gist': recall_dict['memory_summary']['predicted_gist'],
                'elements_encoded': recall_dict['memory_summary']['elements_encoded'],
                'confusion_risk': recall_dict['memory_summary']['confusion_risk'],
                'words_detected': len(ocr_result['words_detected']),
                'legible_words': sum(1 for w in ocr_result['words_detected'] if w['legible']),
                'attention_score': sal_result['attention_score'],
                'suggestions': suggestions[:3],  # Top 3 suggestions
                'video_path': sim_result['video_path'],
                'heatmap_path': f"{output_path}/{job_id}_heatmap.png"
            }

            results.append(result)

            logger.info(f"✓ Recall Score: {result['recall_score']:.1f}/100")
            logger.info(f"✓ Predicted Gist: {result['predicted_gist']}")
            logger.info(f"✓ Video saved: {result['video_path']}")

        except Exception as e:
            logger.error(f"✗ Error processing {image_path.name}: {str(e)}", exc_info=True)
            continue

    return results


def generate_validation_report(results: list, output_dir: str = "assets/outputs"):
    """
    Generate validation report and CSV file.

    Args:
        results: List of validation results
        output_dir: Output directory
    """
    if not results:
        logger.warning("No results to report")
        return

    output_path = Path(output_dir)

    # Generate CSV for validation study
    csv_file = output_path / "validation_results.csv"
    logger.info(f"\nGenerating CSV: {csv_file}")

    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            'sample_id',
            'job_id',
            'filename',
            'recall_score',
            'predicted_gist',
            'top_fix_1',
            'top_fix_2',
            'top_fix_3',
            'video_path',
            'confusion_risk'
        ])

        # Data rows
        for result in results:
            top_fixes = [
                suggestion.get('message', '')[:80] for suggestion in result['suggestions'][:3]
            ]
            # Pad to 3 fixes
            while len(top_fixes) < 3:
                top_fixes.append('')

            writer.writerow([
                result['sample_id'],
                result['job_id'],
                result['filename'],
                f"{result['recall_score']:.1f}",
                result['predicted_gist'],
                top_fixes[0],
                top_fixes[1],
                top_fixes[2],
                result['video_path'],
                f"{result['confusion_risk']:.2f}"
            ])

    # Generate human-readable report
    report_file = output_path / "validation_report.txt"
    logger.info(f"Generating report: {report_file}")

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("RecallLens Validation Report\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Samples Processed: {len(results)}\n")
        f.write("="*80 + "\n\n")

        for result in results:
            f.write(f"SAMPLE {result['sample_id']}: {result['filename']}\n")
            f.write("-"*80 + "\n")
            f.write(f"Recall Score:     {result['recall_score']:.1f}/100\n")
            f.write(f"Predicted Gist:   {result['predicted_gist']}\n")
            f.write(f"Elements Encoded: {', '.join(result['elements_encoded'])}\n")
            f.write(f"Confusion Risk:   {result['confusion_risk']:.2%}\n")
            f.write(f"Words Detected:   {result['words_detected']} ({result['legible_words']} legible)\n")
            f.write(f"Attention Score:  {result['attention_score']:.1f}/100\n")
            f.write(f"\nVideo Path: {result['video_path']}\n")
            f.write(f"\nTop 3 Recommendations:\n")
            for i, suggestion in enumerate(result['suggestions'], 1):
                f.write(f"{i}. [{suggestion['type'].upper()}] {suggestion['message'][:100]}...\n")
                f.write(f"   Impact: {suggestion['estimated_impact']}\n")
            f.write("\n" + "="*80 + "\n\n")

        # Summary statistics
        avg_recall = sum(r['recall_score'] for r in results) / len(results)
        avg_attention = sum(r['attention_score'] for r in results) / len(results)
        avg_confusion = sum(r['confusion_risk'] for r in results) / len(results)

        f.write("SUMMARY STATISTICS\n")
        f.write("="*80 + "\n")
        f.write(f"Average Recall Score:    {avg_recall:.1f}/100\n")
        f.write(f"Average Attention Score: {avg_attention:.1f}/100\n")
        f.write(f"Average Confusion Risk:  {avg_confusion:.2%}\n")
        f.write(f"\nScore Distribution:\n")
        f.write(f"  Excellent (≥75):  {sum(1 for r in results if r['recall_score'] >= 75)} billboards\n")
        f.write(f"  Moderate (55-75): {sum(1 for r in results if 55 <= r['recall_score'] < 75)} billboards\n")
        f.write(f"  Poor (<55):       {sum(1 for r in results if r['recall_score'] < 55)} billboards\n")

    logger.info(f"\n✓ Validation complete!")
    logger.info(f"✓ CSV saved: {csv_file}")
    logger.info(f"✓ Report saved: {report_file}")


def print_human_validation_instructions():
    """Print instructions for human validation study."""
    print("\n" + "="*80)
    print("HUMAN VALIDATION STUDY - INSTRUCTIONS")
    print("="*80)
    print("""
Next Steps:
-----------

1. PREPARE MATERIALS:
   - Locate the 5 simulation videos in backend/assets/outputs/
   - Videos are named: validation_01_simulation.mp4, validation_02_simulation.mp4, etc.
   - Create response sheets (see template below)
   - Set up testing environment (quiet room, computer with video player)

2. RECRUIT 10 TMS MEMBERS:
   - Mix of ages, backgrounds
   - Normal or corrected vision
   - No prior knowledge of the billboards

3. RUN VALIDATION SESSION (per participant):

   Instructions to participant:
   "You'll see 5 billboards as if you're driving past them at highway speed.
    After each 1-second video, write down 3 things you remember.
    You'll only see each billboard once, so pay attention!"

   For each video:
   a) Play video ONCE (1 second)
   b) Immediately ask: "What do you remember?"
   c) Participant writes 3 things
   d) Move to next video (no breaks between videos)

4. RESPONSE SHEET TEMPLATE:

   Participant #: ___    Date: _______    Age: ___

   Billboard 1: 1. ____________________
                2. ____________________
                3. ____________________

   Billboard 2: 1. ____________________
                2. ____________________
                3. ____________________

   [... continues for all 5 billboards]

5. SCORING HUMAN RESPONSES:

   For each participant × billboard:
   - Load predicted_gist from validation_results.csv
   - Compare to their 3 responses
   - Score each element:
     * Exact word match (e.g., "10" matches "10"): 1.0 point
     * Semantic match (e.g., "discount" ~ "sale"): 0.5 points
     * Color match (e.g., "yellow" matches "Yellow"): 0.5 points
     * No match: 0 points
   - Maximum: 3 points per billboard

6. CALCULATE VALIDATION METRICS:

   A. Gist Accuracy: (Total points / (10 participants × 5 billboards × 3)) × 100%
      Target: ≥60% accuracy

   B. Score Calibration: Group billboards by predicted score
      - Excellent (≥75): What % of participants recalled ≥2.25/3 points?
      - Moderate (55-75): What % recalled 1.5-2.25/3 points?
      - Poor (<55): What % recalled <1.5/3 points?
      Target: ≥70% calibration accuracy

   C. Correlation: Pearson correlation between predicted_score and avg_human_score
      Target: r ≥ 0.7

7. REPORT FINDINGS:

   Create summary:
   - Gist accuracy per billboard
   - Calibration table
   - Correlation coefficient
   - Qualitative observations
   - Suggestions for algorithm improvements

8. ITERATE:

   If validation shows poor performance:
   - Adjust sigmoid weights in services/memory.py
   - Tune legibility thresholds in services/ocr.py
   - Refine salience model in services/salience.py
   - Re-run validation with new samples

""")
    print("="*80 + "\n")


def main():
    """Main validation script."""
    print("\n" + "="*80)
    print("RecallLens Validation Script")
    print("="*80 + "\n")

    # Check if samples exist
    samples_dir = Path("assets/samples")
    if not samples_dir.exists() or not any(samples_dir.iterdir()):
        print(f"⚠ No sample images found in {samples_dir}")
        print(f"\nPlease add 5 billboard images to: backend/assets/samples/")
        print(f"Supported formats: .jpg, .jpeg, .png")
        print(f"\nThen run: python validate.py")
        return

    # Run validation
    results = validate_recalllens()

    if results:
        # Generate reports
        generate_validation_report(results)

        # Print human validation instructions
        print_human_validation_instructions()

        # Summary
        print(f"\n{'='*80}")
        print("VALIDATION SUMMARY")
        print(f"{'='*80}")
        print(f"✓ Processed {len(results)} billboard(s)")
        print(f"✓ Average recall score: {sum(r['recall_score'] for r in results) / len(results):.1f}/100")
        print(f"✓ Results saved to: backend/assets/outputs/validation_results.csv")
        print(f"✓ Full report: backend/assets/outputs/validation_report.txt")
        print(f"\n→ Next: Run human validation study with 10 TMS members")
        print(f"{'='*80}\n")
    else:
        print("\n✗ No results generated. Check errors above.")


if __name__ == "__main__":
    main()
