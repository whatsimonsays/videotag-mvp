import base64
import json
import os
import subprocess
import tempfile
import logging
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Tuple

import torch
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image
from transformers import ViTImageProcessor, ViTForImageClassification


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("vidisnap_processor")

model = None
processor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the ViT model and processor on startup."""
    global model, processor
    
    logger.info("Loading ViT model...")
    model_name = "google/vit-base-patch16-224"
    
    try:
        processor = ViTImageProcessor.from_pretrained(model_name)
        model = ViTForImageClassification.from_pretrained(model_name)
        logger.info(f"Model {model_name} loaded successfully")
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        raise
    
    yield
    
    # Cleanup (if needed)
    logger.info("Shutting down processor...")

app = FastAPI(title="VidiSnap Processor", version="1.0.0", lifespan=lifespan)

# Validation functions
def validate_video_file(filename: str) -> None:
    """Validate that the uploaded file is a supported video format."""
    valid_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
    file_ext = os.path.splitext(filename.lower())[1]
    
    if file_ext not in valid_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid video file format. Supported formats: {', '.join(valid_extensions)}"
        )

# File handling functions
async def save_uploaded_video(file: UploadFile) -> str:
    """Save uploaded video file to temporary location."""
    video_path = os.path.join("/tmp", file.filename)
    
    try:
        with open(video_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        return video_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save video: {str(e)}")

def extract_first_frame(video_path: str, filename: str) -> str:
    """Extract the first frame from video using FFmpeg."""
    frame_path = os.path.join("/tmp", f"frame_{filename}.jpg")
    
    ffmpeg_cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", "select=eq(n\\,0)",
        "-vframes", "1",
        frame_path,
        "-y"
    ]
    
    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to extract frame from video: {result.stderr}"
        )
    
    return frame_path

# Image processing functions
def classify_image(image_path: str) -> List[Dict[str, Any]]:
    """Classify image using the loaded ViT model."""
    try:
        # Load and preprocess image
        image = Image.open(image_path)
        inputs = processor(images=image, return_tensors="pt")
        
        # Get predictions
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
        
        # Get top-3 predictions
        probabilities = torch.nn.functional.softmax(logits, dim=-1)
        top3_prob, top3_indices = torch.topk(probabilities, 3)
        
        # Format results
        labels = []
        for i in range(3):
            label = model.config.id2label[top3_indices[0][i].item()]
            score = top3_prob[0][i].item()
            labels.append({"label": label, "score": round(score, 4)})
        
        return labels
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image classification failed: {str(e)}")

def encode_image_to_base64(image_path: str) -> str:
    """Convert image file to base64 string."""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to encode image: {str(e)}")

# Cleanup functions  
def cleanup_temp_files(*file_paths: str) -> None:
    """Safely remove temporary files."""
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.warning(f"Failed to remove {file_path}: {e}")

# Main processing function
@app.post("/process")
async def process_video(file: UploadFile = File(...)):
    """
    Process uploaded video file:
    1. Validate file format
    2. Save video to /tmp
    3. Extract first frame using FFmpeg
    4. Classify frame with ViT model
    5. Return top-3 labels and base64 thumbnail
    """
    video_path = None
    frame_path = None
    
    try:
        # Step 1: Validate file
        validate_video_file(file.filename)
        
        # Step 2: Save uploaded video
        video_path = await save_uploaded_video(file)
        
        # Step 3: Extract first frame
        frame_path = extract_first_frame(video_path, file.filename)
        
        # Step 4: Classify image
        labels = classify_image(frame_path)
        
        # Step 5: Encode thumbnail
        thumbnail_b64 = encode_image_to_base64(frame_path)
        
        # Return response
        response = {
            "labels": labels,
            "thumbnail_b64": thumbnail_b64
        }
        
        return JSONResponse(content=response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected processing error: {e}")
        raise HTTPException(status_code=500, detail="Internal processing error")
    finally:
        # Always cleanup temporary files
        cleanup_temp_files(video_path, frame_path)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "model_loaded": model is not None}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 