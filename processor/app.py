import base64
import json
import os
import subprocess
import tempfile
from typing import List, Dict, Any

import torch
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image
from transformers import ViTImageProcessor, ViTForImageClassification

app = FastAPI(title="VidiSnap Processor", version="1.0.0")

# Global variables for model and processor
model = None
processor = None

@app.on_event("startup")
async def load_model():
    """Load the ViT model and processor on startup."""
    global model, processor
    
    print("Loading ViT model...")
    model_name = "google/vit-base-patch16-224"
    
    try:
        processor = ViTImageProcessor.from_pretrained(model_name)
        model = ViTForImageClassification.from_pretrained(model_name)
        print(f"Model {model_name} loaded successfully")
    except Exception as e:
        print(f"Error loading model: {e}")
        raise

@app.post("/process")
async def process_video(file: UploadFile = File(...)):
    """
    Process uploaded video file:
    1. Save video to /tmp
    2. Extract first frame using FFmpeg
    3. Classify frame with ViT model
    4. Return top-3 labels and base64 thumbnail
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm')):
            raise HTTPException(status_code=400, detail="Invalid video file format")
        
        # Save uploaded video to /tmp
        video_path = os.path.join("/tmp", file.filename)
        with open(video_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Extract first frame using FFmpeg
        frame_path = os.path.join("/tmp", f"frame_{file.filename}.jpg")
        
        ffmpeg_cmd = [
            "ffmpeg", "-i", video_path,
            "-vf", "select=eq(n\\,0)",
            "-vframes", "1",
            frame_path,
            "-y"
        ]
        
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"FFmpeg error: {result.stderr}")
            raise HTTPException(status_code=500, detail="Failed to extract frame from video")
        
        # Load and preprocess image
        image = Image.open(frame_path)
        
        # Prepare image for model
        inputs = processor(images=image, return_tensors="pt")
        
        # Get predictions
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
        
        # Get top-3 predictions
        probabilities = torch.nn.functional.softmax(logits, dim=-1)
        top3_prob, top3_indices = torch.topk(probabilities, 3)
        
        # Get labels
        labels = []
        for i in range(3):
            label = model.config.id2label[top3_indices[0][i].item()]
            score = top3_prob[0][i].item()
            labels.append({"label": label, "score": round(score, 4)})
        
        # Convert thumbnail to base64
        with open(frame_path, "rb") as img_file:
            thumbnail_b64 = base64.b64encode(img_file.read()).decode('utf-8')
        
        # Clean up temporary files
        try:
            os.remove(video_path)
            os.remove(frame_path)
        except:
            pass  # Ignore cleanup errors
        
        # Return response
        response = {
            "labels": labels,
            "thumbnail_b64": thumbnail_b64
        }
        
        return JSONResponse(content=response)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Processing error: {e}")
        raise HTTPException(status_code=500, detail="Internal processing error")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "model_loaded": model is not None}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 