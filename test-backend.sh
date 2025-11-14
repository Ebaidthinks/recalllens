#!/bin/bash
# Test backend deployment
# Usage: ./test-backend.sh https://your-render-url.onrender.com

BACKEND_URL=${1:-https://recalllens-api.onrender.com}

echo "Testing backend at: $BACKEND_URL"
echo ""

echo "1. Testing /health endpoint..."
curl -s "$BACKEND_URL/health" | python3 -m json.tool
echo ""

echo "2. Testing /dubai-presets endpoint..."
curl -s "$BACKEND_URL/dubai-presets" | python3 -m json.tool
echo ""

echo "✅ Backend is healthy!"
