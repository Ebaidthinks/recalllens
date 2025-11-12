"""
RecallLens FastAPI Backend
Simulates how drivers see outdoor ads at highway speeds
"""
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
import uuid
import shutil
from pathlib import Path
import traceback

from config import (
    UPLOAD_DIR, STATIC_DIR, CORS_ORIGINS,
    SPEED_MIN, SPEED_MAX, DISTANCE_MIN, DISTANCE_MAX,
    DWELL_MIN, DWELL_MAX, LIGHTING_OPTIONS, DISTRACTION_OPTIONS,
    ALLOWED_EXTENSIONS, MAX_UPLOAD_SIZE
)
from services.simulate import simulate_view
from services.ocr import extract_text_tokens
from services.salience import analyze_salience
from services.memory import compute_recall
from services.suggest import make_suggestions
from services.report import build_artifacts


# Initialize FastAPI app
app = FastAPI(
    title="RecallLens API",
    description="Analyze outdoor advertisements for driver recall at highway speeds",
    version="1.0.0"
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
app.mount("/files", StaticFiles(directory=str(STATIC_DIR)), name="files")


# Pydantic Models for Request Validation
class AnalysisParams(BaseModel):
    """Parameters for analysis request"""
    speed_kmh: float = Field(
        ...,
        ge=SPEED_MIN,
        le=SPEED_MAX,
        description=f"Vehicle speed in km/h ({SPEED_MIN}-{SPEED_MAX})"
    )
    view_distance_m: float = Field(
        ...,
        ge=DISTANCE_MIN,
        le=DISTANCE_MAX,
        description=f"Viewing distance in meters ({DISTANCE_MIN}-{DISTANCE_MAX})"
    )
    dwell_sec: float = Field(
        ...,
        ge=DWELL_MIN,
        le=DWELL_MAX,
        description=f"Time in view in seconds ({DWELL_MIN}-{DWELL_MAX})"
    )
    lighting: str = Field(
        ...,
        description=f"Lighting condition: {', '.join(LIGHTING_OPTIONS)}"
    )
    phone_distraction: str = Field(
        ...,
        description=f"Phone distraction level: {', '.join(DISTRACTION_OPTIONS)}"
    )

    @validator("lighting")
    def validate_lighting(cls, v):
        if v not in LIGHTING_OPTIONS:
            raise ValueError(f"lighting must be one of {LIGHTING_OPTIONS}")
        return v

    @validator("phone_distraction")
    def validate_distraction(cls, v):
        if v not in DISTRACTION_OPTIONS:
            raise ValueError(f"phone_distraction must be one of {DISTRACTION_OPTIONS}")
        return v


class TokenRecall(BaseModel):
    """Individual token recall probability"""
    token: str
    recall_probability: float


class LegibilityData(BaseModel):
    """Text legibility information"""
    tokens: List[str]
    positions: List[List[float]]
    confidences: List[float]
    legibility_score: float


class SuggestionItem(BaseModel):
    """Single improvement suggestion"""
    category: str
    severity: str
    issue: str
    fix: str
    impact: str


class AnalysisResponse(BaseModel):
    """Response from /analyze endpoint"""
    job_id: str
    recall_score: float
    predicted_gist: str
    cognitive_load: float
    attention_score: float
    legibility_data: LegibilityData
    token_recall: List[TokenRecall]
    suggestions: List[SuggestionItem]
    artifact_urls: Dict[str, str]
    original_params: Dict[str, Any]


# API Endpoints
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "RecallLens API",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "upload_dir": str(UPLOAD_DIR),
        "static_dir": str(STATIC_DIR)
    }


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_advertisement(
    file: UploadFile = File(..., description="Advertisement image file"),
    speed_kmh: float = Form(..., ge=SPEED_MIN, le=SPEED_MAX),
    view_distance_m: float = Form(..., ge=DISTANCE_MIN, le=DISTANCE_MAX),
    dwell_sec: float = Form(..., ge=DWELL_MIN, le=DWELL_MAX),
    lighting: str = Form(...),
    phone_distraction: str = Form(...)
):
    """
    Analyze an outdoor advertisement for driver recall

    This endpoint processes an uploaded advertisement image through a complete
    analysis pipeline:
    1. Simulates motion blur at highway speed
    2. Extracts text via OCR
    3. Generates attention heatmap
    4. Computes recall probability
    5. Provides improvement suggestions
    6. Generates PDF report and comparison video

    Args:
        file: Uploaded advertisement image
        speed_kmh: Vehicle speed (60-140 km/h)
        view_distance_m: Viewing distance (20-60 meters)
        dwell_sec: Time in view (0.5-2.0 seconds)
        lighting: Lighting condition (day/dusk/night)
        phone_distraction: Distraction level (low/med/high)

    Returns:
        Comprehensive analysis with recall scores, legibility data,
        suggestions, and URLs to generated artifacts
    """
    job_id = str(uuid.uuid4())

    try:
        # Validate parameters
        params = AnalysisParams(
            speed_kmh=speed_kmh,
            view_distance_m=view_distance_m,
            dwell_sec=dwell_sec,
            lighting=lighting,
            phone_distraction=phone_distraction
        )

        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # Create job directory
        job_dir = UPLOAD_DIR / job_id
        job_dir.mkdir(exist_ok=True)

        # Save uploaded file
        original_filename = f"original{file_ext}"
        original_path = job_dir / original_filename
        with original_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Validate file size
        if original_path.stat().st_size > MAX_UPLOAD_SIZE:
            shutil.rmtree(job_dir)
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {MAX_UPLOAD_SIZE / (1024*1024):.0f}MB"
            )

        # Step 1: Simulate driver view with motion blur
        simulated_path = simulate_view(
            image_path=str(original_path),
            speed_kmh=params.speed_kmh,
            view_distance_m=params.view_distance_m,
            dwell_sec=params.dwell_sec,
            lighting=params.lighting
        )

        # Step 2: Extract text tokens via OCR
        text_data = extract_text_tokens(str(simulated_path))

        # Step 3: Analyze visual salience and attention
        salience_data = analyze_salience(
            image_path=str(simulated_path),
            phone_distraction=params.phone_distraction
        )

        # Step 4: Compute recall probability
        recall_data = compute_recall(
            text_data=text_data,
            salience_data=salience_data,
            speed_kmh=params.speed_kmh,
            dwell_sec=params.dwell_sec,
            phone_distraction=params.phone_distraction
        )

        # Step 5: Generate improvement suggestions
        suggestions = make_suggestions(
            recall_data=recall_data,
            text_data=text_data,
            salience_data=salience_data,
            speed_kmh=params.speed_kmh,
            dwell_sec=params.dwell_sec
        )

        # Step 6: Build artifacts (PDF report + comparison video)
        artifacts = build_artifacts(
            job_id=job_id,
            original_path=str(original_path),
            simulated_path=simulated_path,
            heatmap_path=salience_data["heatmap_path"],
            recall_data=recall_data,
            text_data=text_data,
            salience_data=salience_data,
            suggestions=suggestions,
            params=params.dict()
        )

        # Copy artifacts to static directory for serving
        static_job_dir = STATIC_DIR / job_id
        static_job_dir.mkdir(exist_ok=True)

        # Copy all generated files
        for src_file in job_dir.glob("*"):
            dst_file = static_job_dir / src_file.name
            shutil.copy2(src_file, dst_file)

        # Copy artifacts
        for key, path in artifacts.items():
            src = Path(path)
            dst = static_job_dir / src.name
            shutil.copy2(src, dst)

        # Build response with artifact URLs
        base_url = "/files"
        artifact_urls = {
            "original": f"{base_url}/{job_id}/{original_filename}",
            "simulated": f"{base_url}/{job_id}/simulated_{original_filename}",
            "heatmap": f"{base_url}/{job_id}/heatmap_simulated_{original_filename}",
            "pdf_report": f"{base_url}/{job_id}/report_{job_id}.pdf",
            "comparison_video": f"{base_url}/{job_id}/comparison_{job_id}.mp4"
        }

        # Build response
        response = AnalysisResponse(
            job_id=job_id,
            recall_score=recall_data["recall_score"],
            predicted_gist=recall_data["predicted_gist"],
            cognitive_load=recall_data["cognitive_load"],
            attention_score=salience_data["attention_score"],
            legibility_data=LegibilityData(**text_data),
            token_recall=[TokenRecall(**t) for t in recall_data["token_recall"]],
            suggestions=[SuggestionItem(**s) for s in suggestions],
            artifact_urls=artifact_urls,
            original_params=params.dict()
        )

        return response

    except ValueError as e:
        # Validation errors
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # Unexpected errors
        print(f"Error processing job {job_id}: {str(e)}")
        print(traceback.format_exc())

        # Clean up on error
        job_dir = UPLOAD_DIR / job_id
        if job_dir.exists():
            shutil.rmtree(job_dir)

        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job and all its artifacts"""
    try:
        # Delete from upload directory
        upload_job_dir = UPLOAD_DIR / job_id
        if upload_job_dir.exists():
            shutil.rmtree(upload_job_dir)

        # Delete from static directory
        static_job_dir = STATIC_DIR / job_id
        if static_job_dir.exists():
            shutil.rmtree(static_job_dir)

        return {"message": f"Job {job_id} deleted successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting job: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    print(f"Unhandled exception: {str(exc)}")
    print(traceback.format_exc())

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
