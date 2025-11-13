"""
RecallLens - FastAPI Backend
Simulates how drivers see outdoor ads at highway speeds
"""

import os
import uuid
import time
import shutil
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from PIL import Image

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

# Import service functions
from services.simulate import simulate_view
from services.ocr import extract_text_tokens
from services.salience import analyze_salience
from services.memory import compute_recall
from services.suggest import make_suggestions
from services.report import build_artifacts

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Analysis timeout (60 seconds)
ANALYSIS_TIMEOUT = 60

# Initialize FastAPI app
app = FastAPI(
    title="RecallLens API",
    description="Analyze outdoor advertisements for driver visibility and recall",
    version="1.0.0"
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup directories
BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "assets" / "uploads"
OUTPUT_DIR = BASE_DIR / "assets" / "outputs"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Mount static files for serving generated assets
app.mount("/files", StaticFiles(directory=str(OUTPUT_DIR)), name="files")


# Pydantic Models
class EnvironmentParams(BaseModel):
    """Environment parameters for simulation"""
    speed_kmh: float = Field(
        ...,
        ge=60,
        le=140,
        description="Vehicle speed in km/h"
    )
    view_distance_m: float = Field(
        ...,
        ge=20,
        le=60,
        description="Viewing distance in meters"
    )
    dwell_sec: float = Field(
        ...,
        ge=0.5,
        le=2.0,
        description="Viewing duration in seconds"
    )
    lighting: str = Field(
        ...,
        description="Lighting condition",
        pattern="^(day|dusk|night)$"
    )
    phone_distraction: str = Field(
        ...,
        description="Phone distraction level",
        pattern="^(low|med|high)$"
    )

    @validator('lighting')
    def validate_lighting(cls, v):
        allowed = ['day', 'dusk', 'night']
        if v not in allowed:
            raise ValueError(f'lighting must be one of {allowed}')
        return v

    @validator('phone_distraction')
    def validate_distraction(cls, v):
        allowed = ['low', 'med', 'high']
        if v not in allowed:
            raise ValueError(f'phone_distraction must be one of {allowed}')
        return v


class TextToken(BaseModel):
    """Represents a detected text element"""
    text: str
    confidence: float
    bbox: List[int]
    legible: bool
    direction: Optional[str] = 'ltr'
    height_px: Optional[int] = 0
    width_px: Optional[int] = 0


class SalienceData(BaseModel):
    """Salience analysis results"""
    heatmap_url: str
    attention_score: float
    hotspot_regions: List[Dict[str, Any]]


class RecallData(BaseModel):
    """Memory recall analysis"""
    recall_score: float = Field(..., ge=0, le=100)
    predicted_gist: str
    retention_factors: Dict[str, float]


class Suggestion(BaseModel):
    """Improvement suggestion"""
    category: str
    priority: str
    description: str
    impact_estimate: str


class AnalysisResponse(BaseModel):
    """Response from the analyze endpoint"""
    job_id: str
    status: str
    recall_score: float
    predicted_gist: str
    legibility_data: Dict[str, Any]
    text_tokens: List[TextToken]
    salience_data: SalienceData
    suggestions: List[Suggestion]
    artifacts: Dict[str, str]
    processing_time_ms: float
    timestamp: str


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "RecallLens API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "analyze": "/analyze",
            "files": "/files/{filename}",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint.
    Validates all critical dependencies and resources.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }

    all_healthy = True

    # Check 1: PaddleOCR availability
    try:
        from paddleocr import PaddleOCR
        health_status["checks"]["paddleocr"] = {
            "status": "ok",
            "message": "PaddleOCR module loaded successfully"
        }
        logger.debug("Health check: PaddleOCR OK")
    except Exception as e:
        health_status["checks"]["paddleocr"] = {
            "status": "error",
            "message": f"PaddleOCR not available: {str(e)}"
        }
        all_healthy = False
        logger.error(f"Health check: PaddleOCR FAILED - {str(e)}")

    # Check 2: PyTorch and ResNet50 model availability
    try:
        import torch
        import torchvision.models as models
        # Just check if we can import, don't actually load the model
        health_status["checks"]["resnet50"] = {
            "status": "ok",
            "message": "PyTorch and ResNet50 available",
            "cuda_available": torch.cuda.is_available()
        }
        logger.debug("Health check: ResNet50 OK")
    except Exception as e:
        health_status["checks"]["resnet50"] = {
            "status": "error",
            "message": f"PyTorch/ResNet50 not available: {str(e)}"
        }
        all_healthy = False
        logger.error(f"Health check: ResNet50 FAILED - {str(e)}")

    # Check 3: FFmpeg availability
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            health_status["checks"]["ffmpeg"] = {
                "status": "ok",
                "message": "FFmpeg available",
                "version": version_line
            }
            logger.debug("Health check: FFmpeg OK")
        else:
            health_status["checks"]["ffmpeg"] = {
                "status": "error",
                "message": "FFmpeg command failed"
            }
            all_healthy = False
            logger.error("Health check: FFmpeg FAILED - command returned non-zero")
    except FileNotFoundError:
        health_status["checks"]["ffmpeg"] = {
            "status": "error",
            "message": "FFmpeg not installed"
        }
        all_healthy = False
        logger.error("Health check: FFmpeg FAILED - not found")
    except Exception as e:
        health_status["checks"]["ffmpeg"] = {
            "status": "error",
            "message": f"FFmpeg check failed: {str(e)}"
        }
        all_healthy = False
        logger.error(f"Health check: FFmpeg FAILED - {str(e)}")

    # Check 4: Write permissions for assets directory
    try:
        test_file = UPLOAD_DIR / ".write_test"
        test_file.write_text("test")
        test_file.unlink()

        test_file = OUTPUT_DIR / ".write_test"
        test_file.write_text("test")
        test_file.unlink()

        health_status["checks"]["filesystem"] = {
            "status": "ok",
            "message": "Write permissions OK",
            "upload_dir": str(UPLOAD_DIR),
            "output_dir": str(OUTPUT_DIR)
        }
        logger.debug("Health check: Filesystem permissions OK")
    except Exception as e:
        health_status["checks"]["filesystem"] = {
            "status": "error",
            "message": f"Write permission error: {str(e)}"
        }
        all_healthy = False
        logger.error(f"Health check: Filesystem FAILED - {str(e)}")

    # Set overall status
    if not all_healthy:
        health_status["status"] = "unhealthy"

    return health_status


def _run_analysis_pipeline(
    job_id: str,
    input_path: Path,
    env_params: EnvironmentParams,
    output_dir: str
) -> Dict[str, Any]:
    """
    Internal function to run the analysis pipeline.
    Separated to enable timeout handling.
    """
    timings = {}

    # Step 1: Simulate view with motion blur
    step_start = time.time()
    logger.info(f"[{job_id}] Step 1/6: Simulating driver view")
    simulation_result = simulate_view(
        str(input_path),
        env_params.dict(),
        job_id,
        output_dir
    )
    timings['simulation'] = time.time() - step_start
    logger.info(f"[{job_id}] Step 1 completed in {timings['simulation']:.2f}s")

    simulated_image_path = simulation_result['representative_frame_path']

    # Step 2: Extract text tokens with OCR
    step_start = time.time()
    logger.info(f"[{job_id}] Step 2/6: Extracting text with OCR")
    ocr_result = extract_text_tokens(simulation_result['frames'])
    timings['ocr'] = time.time() - step_start
    logger.info(f"[{job_id}] Step 2 completed in {timings['ocr']:.2f}s - Found {len(ocr_result['words_detected'])} text elements")

    # Step 3: Analyze visual salience (attention heatmap)
    step_start = time.time()
    logger.info(f"[{job_id}] Step 3/6: Analyzing visual salience")
    salience_data = analyze_salience(
        simulated_image_path,
        job_id,
        output_dir
    )
    timings['salience'] = time.time() - step_start
    logger.info(f"[{job_id}] Step 3 completed in {timings['salience']:.2f}s")

    # Step 4: Compute memory recall score
    step_start = time.time()
    logger.info(f"[{job_id}] Step 4/6: Computing recall score")
    recall_data = compute_recall(
        ocr_result,
        salience_data,
        simulated_image_path
    )
    timings['memory'] = time.time() - step_start
    logger.info(f"[{job_id}] Step 4 completed in {timings['memory']:.2f}s - Score: {recall_data['score']:.1f}")

    # Step 5: Generate improvement suggestions
    step_start = time.time()
    logger.info(f"[{job_id}] Step 5/6: Generating suggestions")
    suggestions = make_suggestions(
        recall_data,
        ocr_result,
        salience_data
    )
    timings['suggestions'] = time.time() - step_start
    logger.info(f"[{job_id}] Step 5 completed in {timings['suggestions']:.2f}s - {len(suggestions)} recommendations")

    # Step 6: Build artifacts (PDF report + comparison video)
    step_start = time.time()
    logger.info(f"[{job_id}] Step 6/6: Building artifacts")
    artifacts = build_artifacts(
        job_id=job_id,
        sim_result=simulation_result,
        sal_result=salience_data,
        ocr_result=ocr_result,
        recall_dict=recall_data,
        suggestions=suggestions,
        output_dir=output_dir
    )
    timings['artifacts'] = time.time() - step_start
    logger.info(f"[{job_id}] Step 6 completed in {timings['artifacts']:.2f}s")

    return {
        'simulation_result': simulation_result,
        'ocr_result': ocr_result,
        'salience_data': salience_data,
        'recall_data': recall_data,
        'suggestions': suggestions,
        'artifacts': artifacts,
        'timings': timings
    }


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_advertisement(
    image: UploadFile = File(..., description="Advertisement image file"),
    speed_kmh: float = Form(..., ge=60, le=140),
    view_distance_m: float = Form(..., ge=20, le=60),
    dwell_sec: float = Form(..., ge=0.5, le=2.0),
    lighting: str = Form(..., pattern="^(day|dusk|night)$"),
    phone_distraction: str = Form(..., pattern="^(low|med|high)$")
):
    """
    Analyze an outdoor advertisement for driver visibility and recall.

    This endpoint simulates how a driver would perceive the ad at highway speeds,
    analyzes text legibility, visual salience, and predicts memory recall.

    Maximum processing time: 60 seconds (will timeout if exceeded)
    """
    start_time = datetime.utcnow()
    job_id = None

    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        logger.info(f"="*80)
        logger.info(f"Starting analysis job {job_id}")
        logger.info(f"Parameters: speed={speed_kmh}km/h, distance={view_distance_m}m, dwell={dwell_sec}s, lighting={lighting}, distraction={phone_distraction}")
        logger.info(f"="*80)

        # Validate image file
        if not image.content_type or not image.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )

        # Create environment parameters
        env_params = EnvironmentParams(
            speed_kmh=speed_kmh,
            view_distance_m=view_distance_m,
            dwell_sec=dwell_sec,
            lighting=lighting,
            phone_distraction=phone_distraction
        )

        # Save uploaded file
        file_extension = Path(image.filename).suffix
        input_path = UPLOAD_DIR / f"{job_id}{file_extension}"

        with open(input_path, "wb") as f:
            content = await image.read()
            f.write(content)
        logger.info(f"[{job_id}] Saved uploaded file: {input_path} ({len(content)} bytes)")

        # Validate image dimensions (should be portrait-ish for lamppost format)
        try:
            with Image.open(input_path) as img:
                width, height = img.size
                aspect_ratio = height / width
                logger.info(f"[{job_id}] Image dimensions: {width}x{height} (aspect ratio: {aspect_ratio:.2f})")

                # Warn if image is landscape (typical billboards are portrait or square)
                if aspect_ratio < 0.7:
                    logger.warning(f"[{job_id}] Image is very landscape ({width}x{height}). Lamppost ads are typically portrait/square. Proceeding anyway.")

                # Check minimum dimensions
                if width < 100 or height < 100:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Image too small ({width}x{height}). Minimum 100x100 pixels required."
                    )

                # Check maximum dimensions (to prevent memory issues)
                if width > 8000 or height > 8000:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Image too large ({width}x{height}). Maximum 8000x8000 pixels."
                    )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[{job_id}] Failed to validate image: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid image file: {str(e)}"
            )

        # Run analysis pipeline with timeout
        logger.info(f"[{job_id}] Starting analysis pipeline (timeout: {ANALYSIS_TIMEOUT}s)")

        try:
            # Use ThreadPoolExecutor to run pipeline with timeout
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    _run_analysis_pipeline,
                    job_id,
                    input_path,
                    env_params,
                    str(OUTPUT_DIR)
                )

                # Wait for result with timeout
                pipeline_result = future.result(timeout=ANALYSIS_TIMEOUT)

        except FuturesTimeoutError:
            logger.error(f"[{job_id}] Analysis timed out after {ANALYSIS_TIMEOUT} seconds")
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail=f"Analysis timed out after {ANALYSIS_TIMEOUT} seconds. Try with a smaller image or different parameters."
            )

        # Extract results from pipeline
        simulation_result = pipeline_result['simulation_result']
        ocr_result = pipeline_result['ocr_result']
        salience_data = pipeline_result['salience_data']
        recall_data = pipeline_result['recall_data']
        suggestions = pipeline_result['suggestions']
        artifacts = pipeline_result['artifacts']
        timings = pipeline_result['timings']

        text_tokens = ocr_result['words_detected']

        # Calculate processing time
        end_time = datetime.utcnow()
        processing_time_ms = (end_time - start_time).total_seconds() * 1000

        # Log timing breakdown
        total_pipeline_time = sum(timings.values())
        logger.info(f"[{job_id}] Timing breakdown:")
        for step, duration in timings.items():
            logger.info(f"  - {step}: {duration:.2f}s ({duration/total_pipeline_time*100:.1f}%)")
        logger.info(f"[{job_id}] Total processing time: {processing_time_ms:.0f}ms")

        # Prepare legibility data
        legibility_data = {
            'total_text_elements': len(text_tokens),
            'legible_count': sum(1 for t in text_tokens if t['legible']),
            'illegible_count': sum(1 for t in text_tokens if not t['legible']),
            'avg_confidence': sum(t['confidence'] for t in text_tokens) / len(text_tokens) if text_tokens else 0,
            'legibility_rate': (sum(1 for t in text_tokens if t['legible']) / len(text_tokens) * 100) if text_tokens else 0,
            'logo_visible': ocr_result['logo_visible'],
            'brand_color_match': ocr_result['brand_color_match']
        }

        logger.info(f"[{job_id}] ✓ Analysis complete - Score: {recall_data['score']:.1f}/100")
        logger.info(f"="*80)

        # Return response
        return AnalysisResponse(
            job_id=job_id,
            status="completed",
            recall_score=recall_data['score'],
            predicted_gist=recall_data['memory_summary']['predicted_gist'],
            legibility_data=legibility_data,
            text_tokens=[TextToken(**t) for t in text_tokens],
            salience_data=SalienceData(**salience_data),
            suggestions=[Suggestion(**s) for s in suggestions],
            artifacts=artifacts,
            processing_time_ms=processing_time_ms,
            timestamp=end_time.isoformat()
        )

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except FileNotFoundError as e:
        logger.error(f"File not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Required file not found: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom exception handler for HTTP errors"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Catch-all exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
