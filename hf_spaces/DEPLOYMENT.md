# Deploying RecallLens to Hugging Face Spaces

Get your RecallLens app live with a public URL in **5 minutes**!

## 🚀 Quick Deploy (Recommended)

### Step 1: Create Hugging Face Account

1. Go to **[huggingface.co](https://huggingface.co/join)**
2. Sign up (free account)
3. Verify your email

### Step 2: Create a New Space

1. Go to **[huggingface.co/new-space](https://huggingface.co/new-space)**
2. Fill in the details:
   - **Space name:** `recalllens` (or your preferred name)
   - **License:** MIT
   - **Select the SDK:** Gradio
   - **Space hardware:** CPU basic (free)
   - **Visibility:** Public

3. Click **"Create Space"**

### Step 3: Upload Files

You have two options:

#### Option A: Upload via Web Interface (Easiest)

1. In your new Space, click **"Files"** tab
2. Click **"Add file"** → **"Upload files"**
3. Upload ALL files from `hf_spaces/` directory:
   - `app.py`
   - `requirements.txt`
   - `README.md`
   - `packages.txt`
   - `.gitignore`
   - `services/` folder (all .py files)
   - `assets/` folder (with .gitkeep files)

4. Click **"Commit changes to main"**

#### Option B: Git Clone and Push (Advanced)

```bash
# Clone your new Space repo
git clone https://huggingface.co/spaces/YOUR_USERNAME/recalllens
cd recalllens

# Copy all files from hf_spaces/
cp -r /path/to/recalllens/hf_spaces/* .

# Commit and push
git add .
git commit -m "Initial RecallLens deployment"
git push
```

### Step 4: Wait for Build

1. HF Spaces will automatically build your app (5-10 minutes)
2. Watch the **"Logs"** tab to see build progress
3. You'll see:
   - ✓ Installing system dependencies (ffmpeg, OpenCV libs)
   - ✓ Installing Python packages (PyTorch, PaddleOCR, Gradio)
   - ✓ Starting Gradio app on port 7860
   - ✓ Running on http://0.0.0.0:7860

### Step 5: Get Your Public URL! 🎉

Once the build completes, your app is live at:

```
https://huggingface.co/spaces/YOUR_USERNAME/recalllens
```

**Share this URL with anyone!** No login required to use the app.

---

## 📊 What You'll Get

Your live RecallLens Space includes:

- ✅ Full billboard analysis pipeline
- ✅ Dubai road presets (SZR, Al Khail, JBR, Marina)
- ✅ Image upload and processing
- ✅ Attention heatmaps
- ✅ Arabic + English OCR
- ✅ PDF report generation
- ✅ Video simulations
- ✅ Public URL you can share

---

## 🔧 Configuration

### Hardware Options

**Free Tier (CPU basic):**
- **Cost:** $0/month
- **Specs:** 2 vCPU, 16GB RAM
- **Good for:** Testing, demos, personal use
- **Limitations:** May be slow for large images

**Upgraded (CPU basic - persistent):**
- **Cost:** $5/month
- **Specs:** Same as free, but always running
- **Good for:** Production use without cold starts

**GPU T4 (if you need speed):**
- **Cost:** $0.60/hour (billed per second)
- **Specs:** NVIDIA T4 GPU, 16GB VRAM
- **Good for:** Fast processing, high traffic
- **Note:** Requires payment method

### Environment Variables

No environment variables needed! Everything is configured in `app.py`.

---

## 🧪 Testing Your Deployment

### 1. Basic Health Check

1. Open your Space URL
2. You should see the RecallLens interface
3. Check that all UI elements load correctly

### 2. Test Analysis

1. Upload a test billboard image (portrait format)
2. Select "Sheikh Zayed Road (SZR)" preset
3. Click "Analyze Billboard"
4. Wait 30-60 seconds (first run loads models)
5. Verify you get:
   - ✓ Recall score (0-100)
   - ✓ Simulated view image
   - ✓ Attention heatmap
   - ✓ Extracted text
   - ✓ Optimization suggestions
   - ✓ PDF download

### 3. Test Dubai Features

1. Try different road presets
2. Test Dubai-specific lighting (dubai_day, dubai_dusk)
3. Upload an image with Arabic text
4. Verify language analysis works

---

## 🐛 Troubleshooting

### Build Fails with "Out of Memory"

**Solution:** Upgrade to persistent CPU basic ($5/month) or use GPU

### App Shows "Application Startup Failed"

**Check logs for errors:**
1. Go to your Space
2. Click "Logs" tab
3. Look for error messages

**Common issues:**
- Missing file in upload (check all files are uploaded)
- Syntax error in app.py (verify file is correct)
- Missing system dependency (check packages.txt)

### Analysis Takes Too Long

**First run is slow (30-60s)** because it loads:
- PyTorch models
- PaddleOCR models
- Grad-CAM models

**Subsequent runs are faster (3-5s)**

**To speed up:**
- Upgrade to GPU T4 hardware
- Or use smaller images (resize to 1000px height)

### Models Not Loading

**Error:** "Cannot load PaddleOCR model"

**Solution:**
1. Check that `packages.txt` includes all OpenCV dependencies
2. Verify `requirements.txt` has correct PaddleOCR version
3. Try rebuilding the Space (click "Factory reboot" in Settings)

### PDF Generation Fails

**Error:** "ReportLab cannot create PDF"

**Solution:**
- Check that `/assets/outputs/` directory exists
- Verify write permissions (should be automatic on HF Spaces)
- Check logs for specific ReportLab errors

---

## 🎨 Customization

### Update the Interface

Edit `app.py`:

```python
# Change theme
demo = gr.Blocks(theme=gr.themes.Monochrome())  # Dark theme

# Change title
gr.Markdown("# Your Custom Title")

# Add more presets
DUBAI_PRESETS["Your Road"] = {
    "speed_kmh": 100.0,
    # ...
}
```

Commit and push → Space auto-rebuilds

### Add Sample Images

1. Upload sample images to `assets/samples/`
2. Modify `app.py` to show examples:

```python
gr.Examples(
    examples=["assets/samples/billboard1.jpg"],
    inputs=image_input
)
```

### Change Model Settings

Edit service files:
- `services/salience.py` - Change attention model
- `services/ocr.py` - OCR language settings
- `services/memory.py` - Recall score weights

---

## 📈 Monitoring

### View Usage Stats

1. Go to your Space
2. Click "Analytics" tab
3. See:
   - Total views
   - Unique users
   - Requests over time

### Check Logs

Real-time logs show:
- Analysis requests
- Processing time
- Errors and warnings

### Embed in Website

```html
<iframe
  src="https://YOUR_USERNAME-recalllens.hf.space"
  width="100%"
  height="800px"
></iframe>
```

---

## 💰 Cost Comparison

| Tier | Cost | Specs | Use Case |
|------|------|-------|----------|
| **Free CPU** | $0/month | 2 vCPU, 16GB RAM, cold starts | Testing, demos |
| **Persistent CPU** | $5/month | Always-on, no cold starts | Production |
| **GPU T4** | ~$43/month | NVIDIA T4, fast processing | High traffic |

**Recommendation:** Start with free, upgrade to persistent CPU ($5/mo) if you get regular traffic.

---

## 🔒 Security & Privacy

### What Happens to Uploaded Images?

- Images are processed in-memory
- Temporarily saved to `assets/uploads/`
- Deleted after analysis completes
- Not stored permanently
- Not used for training

### Who Can Access the App?

- **Public Spaces:** Anyone with the URL
- **Private Spaces:** Only you (change in Space settings)

### API Access

HF Spaces provides automatic API:

```python
from gradio_client import Client

client = Client("YOUR_USERNAME/recalllens")
result = client.predict(
    image="path/to/billboard.jpg",
    speed_kmh=100,
    # ...
)
```

---

## 🚀 Next Steps

### 1. Share Your Space

- Add to Hugging Face community
- Share on social media
- Embed in your portfolio

### 2. Collect Feedback

- Enable discussions on your Space
- Monitor analytics
- Iterate based on user feedback

### 3. Upgrade Features

- Add more Dubai locations
- Support video upload (analyze multiple billboards)
- Add comparison mode (A/B test designs)
- Integrate with design tools

---

## 📚 Resources

- **Hugging Face Spaces Docs:** https://huggingface.co/docs/hub/spaces
- **Gradio Docs:** https://gradio.app/docs
- **RecallLens GitHub:** https://github.com/Ebaidthinks/recalllens
- **Support:** Open an issue on GitHub

---

## ✅ Deployment Checklist

- [ ] Created Hugging Face account
- [ ] Created new Space (Gradio SDK)
- [ ] Uploaded all files from `hf_spaces/`
- [ ] Build completed successfully
- [ ] Tested billboard analysis
- [ ] Verified PDF download works
- [ ] Tested Dubai presets
- [ ] Tested Arabic text detection
- [ ] Got public URL
- [ ] Shared with team/clients

**Your RecallLens Space is live! 🎉**

URL: `https://huggingface.co/spaces/YOUR_USERNAME/recalllens`
