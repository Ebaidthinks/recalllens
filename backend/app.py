"""
RecallLens - FastAPI Backend
Simulates how drivers see outdoor ads at highway speeds
"""

import os
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import logging

# Import service functions
from services.simulate import simulate_view
from services.ocr import extract_text_tokens
from services.salience import analyze_salience
from services.memory import compute_recall
from services.suggest import make_suggestions
from services.report import build_artifacts

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
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
    """
    start_time = datetime.utcnow()

    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        logger.info(f"Starting analysis job {job_id}")

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
        logger.info(f"Saved uploaded file: {input_path}")

        # Step 1: Simulate view with motion blur
        logger.info("Step 1: Simulating driver view")
        simulation_result = simulate_view(
            str(input_path),
            env_params.dict(),
            job_id,
            str(OUTPUT_DIR)
        )
        simulated_image_path = simulation_result['representative_frame_path']

        # Step 2: Extract text tokens with OCR
        logger.info("Step 2: Extracting text with OCR")
        ocr_result = extract_text_tokens(simulation_result['frames'])
        text_tokens = ocr_result['words_detected']

        # Step 3: Analyze visual salience (attention heatmap)
        logger.info("Step 3: Analyzing visual salience")
        salience_data = analyze_salience(
            simulated_image_path,
            job_id,
            str(OUTPUT_DIR)
        )

        # Step 4: Compute memory recall score
        logger.info("Step 4: Computing recall score")
        recall_data = compute_recall(
            ocr_result,
            salience_data,
            simulated_image_path
        )

        # Step 5: Generate improvement suggestions
        logger.info("Step 5: Generating suggestions")
        suggestions = make_suggestions(
            recall_data,
            ocr_result,
            salience_data
        )

        # Step 6: Build artifacts (PDF report + comparison video)
        logger.info("Step 6: Building artifacts")
        artifacts = build_artifacts(
            job_id=job_id,
            original_path=str(input_path),
            simulated_path=simulated_image_path,
            analysis_data={
                'recall_data': recall_data,
                'text_tokens': text_tokens,
                'salience_data': salience_data,
                'suggestions': suggestions,
                'env_params': env_params.dict()
            },
            output_dir=str(OUTPUT_DIR)
        )

        # Add simulation video to artifacts if available
        if simulation_result['video_path']:
            artifacts['simulation_video'] = f"/files/{Path(simulation_result['video_path']).name}"

        # Calculate processing time
        end_time = datetime.utcnow()
        processing_time_ms = (end_time - start_time).total_seconds() * 1000

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

        logger.info(f"Analysis complete for job {job_id}")

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
