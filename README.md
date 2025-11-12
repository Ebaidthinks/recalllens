# RecallLens

A tool that simulates how drivers see outdoor advertisements at highway speeds and predicts recall probability.

## Overview

RecallLens analyzes outdoor ads by simulating real-world viewing conditions including:
- Motion blur from vehicle speed
- Viewing distance effects
- Attention distribution (heatmaps)
- Cognitive load under distraction
- Text legibility at speed

The system provides actionable suggestions to improve ad recall rates.

## Architecture

```
recalllens/
├── backend/
│   ├── app.py              # FastAPI application
│   ├── config.py           # Configuration settings
│   ├── requirements.txt    # Python dependencies
│   ├── services/
│   │   ├── simulate.py     # Motion blur simulation
│   │   ├── ocr.py          # Text extraction (PaddleOCR)
│   │   ├── salience.py     # Attention heatmaps (GradCAM)
│   │   ├── memory.py       # Recall scoring
│   │   ├── suggest.py      # Improvement suggestions
│   │   └── report.py       # PDF/video generation
│   ├── uploads/            # Temporary job storage
│   └── static/             # Served artifacts
```

## Installation

### 1. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Install System Dependencies

**For PaddleOCR:**
```bash
# Ubuntu/Debian
apt-get install libgomp1

# macOS
brew install libomp
```

**For video generation (optional):**
```bash
# Ubuntu/Debian
apt-get install ffmpeg

# macOS
brew install ffmpeg
```

## Running the Server

### Development Mode

```bash
cd backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
cd backend
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs (Swagger UI)
- **Files**: http://localhost:8000/files

## API Endpoints

### POST /analyze

Analyze an outdoor advertisement image.

**Request:**
- `file`: Image file (jpg, png, bmp, tiff)
- `speed_kmh`: Vehicle speed (60-140 km/h)
- `view_distance_m`: Viewing distance (20-60 meters)
- `dwell_sec`: Time in view (0.5-2.0 seconds)
- `lighting`: Lighting condition (`day`, `dusk`, `night`)
- `phone_distraction`: Distraction level (`low`, `med`, `high`)

**Response:**
```json
{
  "job_id": "uuid",
  "recall_score": 0.72,
  "predicted_gist": "TOP REMEMBERED WORDS",
  "cognitive_load": 0.45,
  "attention_score": 0.68,
  "legibility_data": {
    "tokens": ["WORD1", "WORD2"],
    "positions": [[x1, y1, x2, y2], ...],
    "confidences": [0.95, 0.87],
    "legibility_score": 0.81
  },
  "token_recall": [
    {
      "token": "WORD1",
      "recall_probability": 0.85
    }
  ],
  "suggestions": [
    {
      "category": "text",
      "severity": "high",
      "issue": "Low text legibility at high speed",
      "fix": "Increase font size by 2-3x",
      "impact": "Could improve recall by 30-40%"
    }
  ],
  "artifact_urls": {
    "original": "/files/{job_id}/original.jpg",
    "simulated": "/files/{job_id}/simulated_original.jpg",
    "heatmap": "/files/{job_id}/heatmap_simulated_original.jpg",
    "pdf_report": "/files/{job_id}/report_{job_id}.pdf",
    "comparison_video": "/files/{job_id}/comparison_{job_id}.mp4"
  },
  "original_params": {...}
}
```

### GET /health

Health check endpoint.

### DELETE /jobs/{job_id}

Delete a job and all its artifacts.

## Usage Examples

### cURL

```bash
curl -X POST "http://localhost:8000/analyze" \
  -F "file=@advertisement.jpg" \
  -F "speed_kmh=80" \
  -F "view_distance_m=30" \
  -F "dwell_sec=1.0" \
  -F "lighting=day" \
  -F "phone_distraction=low"
```

### Python

```python
import requests

url = "http://localhost:8000/analyze"

files = {"file": open("ad.jpg", "rb")}
data = {
    "speed_kmh": 80,
    "view_distance_m": 30,
    "dwell_sec": 1.0,
    "lighting": "day",
    "phone_distraction": "low"
}

response = requests.post(url, files=files, data=data)
result = response.json()

print(f"Recall Score: {result['recall_score']:.2%}")
print(f"Predicted Gist: {result['predicted_gist']}")
print(f"PDF Report: {result['artifact_urls']['pdf_report']}")
```

### JavaScript (Fetch API)

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('speed_kmh', 80);
formData.append('view_distance_m', 30);
formData.append('dwell_sec', 1.0);
formData.append('lighting', 'day');
formData.append('phone_distraction', 'low');

fetch('http://localhost:8000/analyze', {
  method: 'POST',
  body: formData
})
  .then(response => response.json())
  .then(data => {
    console.log('Recall Score:', data.recall_score);
    console.log('Predicted Gist:', data.predicted_gist);
    console.log('PDF Report:', data.artifact_urls.pdf_report);
  });
```

## Testing

Run the test suite:

```bash
cd backend
python test_api.py
```

## Parameters Explained

### speed_kmh (60-140)
- **60-80**: City/suburban speeds - better recall
- **80-100**: Highway speeds - moderate recall
- **100-140**: High-speed highway - challenging recall

### view_distance_m (20-60)
- **20-30**: Close viewing - better legibility
- **30-45**: Medium distance - typical billboards
- **45-60**: Far viewing - challenging legibility

### dwell_sec (0.5-2.0)
- **0.5-1.0**: Quick glance
- **1.0-1.5**: Normal viewing
- **1.5-2.0**: Extended attention

### lighting
- **day**: Full daylight - best visibility
- **dusk**: Reduced brightness - moderate visibility
- **night**: Low light - challenging visibility

### phone_distraction
- **low**: Minimal distraction - full attention
- **med**: Moderate distraction - 60% attention
- **high**: Heavy distraction - 30% attention

## Output Artifacts

For each analysis, RecallLens generates:

1. **Simulated View**: How the ad appears with motion blur and distance effects
2. **Attention Heatmap**: Where drivers look (visual salience map)
3. **PDF Report**: Comprehensive analysis with scores and suggestions
4. **Comparison Video**: Side-by-side original/simulated/heatmap

All artifacts are accessible via `/files/{job_id}/` URLs.

## CORS Configuration

Default CORS origins (configured in `config.py`):
- http://localhost:3000
- http://localhost:8000
- http://127.0.0.1:3000
- http://127.0.0.1:8000

Modify `CORS_ORIGINS` in `config.py` to add additional origins.

## Scoring Methodology

### Recall Score (0-1)
Composite score based on:
- **Text Legibility** (30%): OCR confidence and text size
- **Visual Attention** (30%): Salience map intensity
- **Speed Factor** (15%): Inverse relationship to speed
- **Dwell Time** (15%): Encoding time availability
- **Distraction** (10%): Attention availability

### Cognitive Load (0-1)
Processing difficulty based on:
- **Text Complexity** (40%): Word count
- **Speed Load** (30%): Processing time pressure
- **Distraction Load** (30%): Available attention

### Legibility Score (0-1)
Text readability based on:
- **OCR Confidence** (50%): Detection accuracy
- **Token Count** (30%): Expected vs actual
- **Text Size** (20%): Relative to image area

## Troubleshooting

### PaddleOCR Issues
If OCR fails:
```bash
# Clear PaddleOCR cache
rm -rf ~/.paddleocr/
```

### PyTorch Issues
If attention heatmap fails:
```bash
# Install/reinstall PyTorch
pip install torch torchvision --force-reinstall
```

### Video Generation Issues
If video creation fails:
```bash
# Check ffmpeg installation
ffmpeg -version

# Install/reinstall ffmpeg-python
pip install ffmpeg-python --force-reinstall
```

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please open an issue or submit a pull request.

## Support

For issues and questions, please open a GitHub issue.
