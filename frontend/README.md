# RecallLens Frontend

Professional React frontend for RecallLens billboard recall prediction system.

## Tech Stack

- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first styling
- **Axios** - HTTP client for API calls
- **Inter Font** - Professional typography

## Features

### Upload Section
- Drag-and-drop file upload
- Image preview
- Support for JPG, PNG formats

### Environment Controls
- Speed slider (60-140 km/h)
- Viewing distance slider (20-60m)
- Dwell time slider (0.5-2.0s)
- Lighting conditions (day/dusk/night)
- Phone distraction levels (low/med/high)

### Results Dashboard
- **Animated Score Dial** - Circular progress indicator with color coding
- **Predicted Gist** - What drivers will remember
- **Image Comparison** - Original vs Simulated vs Heatmap
- **Tabbed Analysis**:
  - Legibility: Text detection results with confidence scores
  - Attention: Visual salience heatmap regions
  - Memory: What gets encoded vs forgotten
  - Fixes: Prioritized recommendations with impact estimates
- **PDF Download** - Full professional report

## Development

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Environment

The frontend expects the backend API to be running at:
```
http://localhost:8000
```

Make sure the FastAPI backend is running before starting the frontend.

## Backend Integration

The app makes POST requests to `/analyze` with:
- `file`: Image file (multipart/form-data)
- `speed_kmh`: Vehicle speed
- `view_distance_m`: Distance to billboard
- `dwell_sec`: Exposure time
- `lighting`: Lighting conditions
- `phone_distraction`: Distraction level

## Design System

### Colors
- Primary: Blue (#2563eb) to Indigo (#4f46e5) gradient
- Success: Green (#10b981)
- Warning: Yellow (#f59e0b)
- Danger: Red (#ef4444)

### Score Color Coding
- Green (≥75): Excellent recall
- Yellow (55-75): Moderate recall
- Red (<55): Poor recall

## Components

- `App.jsx` - Main application with state management
- `UploadSection.jsx` - File upload with drag-and-drop
- `EnvironmentControls.jsx` - Parameter sliders and dropdowns
- `ResultsDashboard.jsx` - Main results container
- `ScoreDial.jsx` - Animated circular score indicator
- `ImageComparison.jsx` - Side-by-side image viewer
- `LegibilityTab.jsx` - Text detection results table
- `AttentionTab.jsx` - Attention heatmap analysis
- `MemoryTab.jsx` - Memory encoding breakdown
- `FixesTab.jsx` - Prioritized recommendations

## Browser Support

Modern browsers with ES6+ support:
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## Performance

- Code splitting with Vite
- Lazy loading of components
- Optimized image handling
- Gzip compression enabled

## License

Part of the RecallLens project.
