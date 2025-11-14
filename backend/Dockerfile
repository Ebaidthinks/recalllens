# Build stage with Python 3.10
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for OpenCV and other libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgthread-2.0-0 \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies in stages to avoid memory issues on free tier
# Stage 1: Install PyTorch CPU-only (lighter, faster for free tier)
RUN pip install --no-cache-dir \
    torch==2.1.0 \
    torchvision==0.16.0 \
    --index-url https://download.pytorch.org/whl/cpu

# Stage 2: Install pytorch-grad-cam (requires torch to be installed first)
RUN pip install --no-cache-dir pytorch-grad-cam

# Stage 3: Install other ML dependencies
RUN pip install --no-cache-dir \
    numpy \
    opencv-python-headless \
    Pillow \
    paddleocr \
    scikit-image \
    scipy \
    transformers

# Stage 4: Install FastAPI and remaining dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    reportlab \
    pydantic \
    pydantic-settings \
    python-multipart \
    ffmpeg-python

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p assets/uploads assets/outputs assets/samples

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
