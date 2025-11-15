---
title: RecallLens - Billboard Recall Prediction
emoji: 🎯
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.12.0
app_file: app.py
pinned: false
license: mit
---

# 🎯 RecallLens - Billboard Recall Prediction

**Predict how memorable your billboard will be using AI-powered analysis.**

RecallLens simulates real-world viewing conditions and predicts memory recall for outdoor advertising billboards. Upload your billboard design and get instant feedback on visibility, readability, and memorability.

## ✨ Features

- **🚗 Real Viewing Simulation**: Account for speed, distance, and lighting conditions
- **🧠 Memory Recall Prediction**: Science-based scoring (0-100)
- **🔥 Visual Attention Heatmaps**: See where drivers look using ResNet50 + Grad-CAM
- **📝 Multi-Language OCR**: Arabic + English text extraction with PaddleOCR
- **🌍 Dubai-Specific Presets**: Optimized for Sheikh Zayed Road, Al Khail Road, JBR, and Marina
- **💡 Optimization Suggestions**: AI-generated recommendations to improve recall
- **📄 PDF Reports**: Professional analysis reports for stakeholders

## 🎯 Use Cases

- **Outdoor Advertising Agencies**: Test billboard designs before printing
- **Brand Managers**: Optimize campaign creative for maximum recall
- **Media Buyers**: Compare billboard locations by visibility
- **Designers**: Validate text readability and visual hierarchy

## 🚀 How to Use

1. **Upload** a billboard image (portrait format recommended for lamppost billboards)
2. **Select** environment settings:
   - Choose a Dubai road preset (SZR, Al Khail, JBR, Marina)
   - Or customize speed, distance, lighting, and distraction levels
3. **Click** "Analyze Billboard"
4. **Review** results:
   - Recall Score (0-100)
   - Simulated view (how drivers see it)
   - Attention heatmap (where they look)
   - Extracted text with language analysis
   - Design optimization suggestions
5. **Download** the PDF report

## 🔬 Technology Stack

### Computer Vision & ML
- **Simulation**: OpenCV for atmospheric effects (glare, blur, contrast)
- **OCR**: PaddleOCR (Arabic + English text detection)
- **Attention**: ResNet50 + Grad-CAM for visual saliency
- **Video**: FFmpeg for driving simulation videos

### Memory Recall Model
- **Exposure Time**: Based on speed and distance
- **Dwell Time**: Visual fixation duration
- **Salience Score**: Attention-grabbing elements
- **Text Readability**: OCR confidence and word count
- **Environmental Factors**: Lighting, distraction, viewing angle

### Scoring Formula
```
Recall Score = sigmoid(
    exposure_weight * exposure_norm +
    dwell_weight * dwell_norm +
    salience_weight * salience_norm +
    text_weight * text_norm -
    distraction_penalty
)
```

## 🌍 Dubai-Specific Features

### Road Presets
1. **Sheikh Zayed Road (SZR)**: 120 km/h, high-speed highway
2. **Al Khail Road**: 100 km/h, major arterial
3. **JBR Beach Road**: 60 km/h, urban with pedestrians
4. **Dubai Marina**: 40 km/h, slow traffic with high attention

### Lighting Effects
- **Dubai Day**: Intense sunlight with high glare simulation
- **Dubai Dusk**: Golden hour with warm tint
- **Dubai Night**: LED brightness compensation for illuminated billboards

### Language Support
- Detects Arabic vs English text ratio
- Identifies mixed EN/AR copy (common in Dubai)
- Analyzes text direction (RTL for Arabic)
- Recognizes Arabic numerals (٠-٩)

## 📊 Output

### Recall Score
- **90-100**: Excellent (highly memorable)
- **70-89**: Good (above average recall)
- **50-69**: Fair (moderate recall)
- **30-49**: Poor (low recall)
- **0-29**: Very Poor (likely forgotten)

### PDF Report Includes
- Original billboard image
- Simulated view under selected conditions
- Attention heatmap overlay
- Extracted text with confidence scores
- Language analysis (Arabic/English mix)
- Recall score with rating
- Design optimization suggestions
- Environmental parameters used

## 🛠️ Pipeline Steps

1. **Simulation**: Apply viewing conditions (speed blur, distance scaling, lighting effects)
2. **OCR**: Extract text with PaddleOCR (Arabic + English)
3. **Salience**: Compute attention heatmap with ResNet50 + Grad-CAM
4. **Memory**: Predict recall score using multi-factor model
5. **Suggestions**: Generate AI-powered optimization recommendations
6. **Artifacts**: Create PDF report and video simulation

## 🎨 Design Tips

### For Maximum Recall
- ✅ Use high-contrast colors
- ✅ Keep text large and bold (readable from 30-40m)
- ✅ Limit text to 5-7 words maximum
- ✅ Place key message in upper-left quadrant (first fixation point)
- ✅ Use simple, recognizable imagery
- ✅ Ensure text is readable in Dubai's bright sunlight

### To Avoid
- ❌ Small or thin fonts
- ❌ Low contrast (e.g., light gray on white)
- ❌ Too much text (cognitive overload)
- ❌ Complex imagery requiring sustained attention
- ❌ Important details at edges (peripheral vision limits)

## 📚 Research Background

RecallLens is based on research in:
- **Visual Attention**: Itti & Koch saliency models
- **Memory Formation**: Ebbinghaus forgetting curve
- **Reading in Motion**: Legibility studies for highway signage
- **Outdoor Advertising**: OAAA (Outdoor Advertising Association) guidelines
- **Dubai Context**: Local traffic patterns and lighting conditions

## 🔒 Privacy

- Images are processed in-memory and not permanently stored
- No data is collected or shared
- All processing happens on Hugging Face infrastructure
- Temporary files are cleaned up after analysis

## 📄 License

MIT License - Free for commercial and personal use

## 🙏 Acknowledgments

Built with:
- Gradio by Hugging Face
- PaddleOCR by PaddlePaddle
- PyTorch & torchvision
- OpenCV
- ReportLab

## 🐛 Issues & Feedback

Found a bug or have a suggestion? Open an issue on GitHub!

## 🚀 About

RecallLens helps outdoor advertising professionals make data-driven creative decisions. By simulating real viewing conditions and predicting memory recall, we take the guesswork out of billboard design.

Perfect for the Dubai market where high-speed roads, intense sunlight, and bilingual messaging create unique challenges for outdoor advertising.

---

**Try it now!** Upload your billboard and see how memorable it is. 🎯
