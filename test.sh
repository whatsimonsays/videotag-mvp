#!/bin/bash

# Test script for VidiSnap MVP
# Make sure Docker Desktop is running and services are up

echo "Testing VidiSnap API..."

# Test health endpoint (if available)
echo "Testing API health..."
curl -s http://localhost:8080/health || echo "API not ready yet"

echo ""
echo "To test with a video file, run:"
echo "curl -X POST -F file=@your_video.mp4 http://localhost:8080/analyze | jq"
echo ""
echo "Make sure to:"
echo "1. Start Docker Desktop"
echo "2. Run: docker compose up --build"
echo "3. Wait for services to be ready"
echo "4. Use a small MP4 file (< 10MB) for testing" 