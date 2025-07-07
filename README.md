# VidiSnap MVP

A microservice-based video analysis system that extracts the first frame from uploaded videos, classifies it using a Hugging Face ViT model, and returns top-3 labels with a base-64 thumbnail.

## Architecture

- **Go API** (port 8080): Handles file uploads and forwards to processor
- **Python FastAPI Processor** (port 8000): Extracts frames and performs image classification
- **Docker Compose**: Orchestrates both services

## Quick Start

1. Build and run the services:
```bash
docker compose up --build
```

2. Test with a sample video:
```bash
curl -X POST -F file=@sample.mp4 http://localhost:8080/analyze | jq
```

## API Endpoints

- `POST /analyze`: Upload a video file for analysis
  - Returns JSON with top-3 classification labels and base-64 thumbnail

## Response Format

```json
{
  "labels": [
    {"label": "cat", "score": 0.94},
    {"label": "dog", "score": 0.03},
    {"label": "animal", "score": 0.02}
  ],
  "thumbnail_b64": "iVBORw0KGgoAAAANSUhEUgAA..."
}
```

## Requirements

- Docker Desktop
- macOS/Linux
- Sample MP4 file for testing (< 10MB recommended)
