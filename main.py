"""
Voice Clone Singer Backend
FastAPI server for voice conversion pipeline
"""

import os
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime
import uuid

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import aiofiles

from uvr_infer import separate_vocals
from rvc_infer import convert_voice
from mix import mix_tracks

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Voice Clone Singer API",
    description="Backend for voice conversion in songs",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
MODELS_DIR = Path("models")

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)

# Mount static files for outputs
app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")

# Store voice profiles
VOICE_PROFILES = {
    "default": {
        "name": "Default Voice",
        "model_path": None,
        "index_path": None,
        "method": "basic"
    }
}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/voice")
async def upload_voice(file: UploadFile = File(...)):
    """
    Upload voice sample for voice profile creation
    
    Args:
        file: Audio file (MP3, WAV, M4A)
        
    Returns:
        JSON with voiceProfileId
    """
    try:
        logger.info(f"Received voice upload: {file.filename}")
        
        # Generate unique profile ID
        profile_id = str(uuid.uuid4())[:8]
        
        # Save uploaded file
        file_path = UPLOAD_DIR / f"{profile_id}_voice_sample.m4a"
        
        async with aiofiles.open(file_path, "wb") as f:
            content = await file.read()
            await f.write(content)
        
        logger.info(f"Voice sample saved: {file_path}")
        
        # In production, you would:
        # 1. Process the voice sample
        # 2. Create a voice profile/model
        # 3. Store model files
        
        # For MVP, just store the file and return profile ID
        VOICE_PROFILES[profile_id] = {
            "name": f"Voice Profile {profile_id}",
            "model_path": str(file_path),
            "index_path": None,
            "method": "basic"
        }
        
        return {
            "voiceProfileId": profile_id,
            "message": "Voice sample uploaded successfully"
        }
        
    except Exception as e:
        logger.error(f"Error uploading voice: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process")
async def process_song(
    song: UploadFile = File(...),
    voiceProfileId: str = Form(...),
    title: str = Form(default="Converted Song")
):
    """
    Process song with voice conversion
    
    Args:
        song: Audio file (MP3, WAV, M4A)
        voiceProfileId: ID of voice profile to use
        title: Title of the song
        
    Returns:
        JSON with audioUrl
    """
    try:
        logger.info(f"Processing song: {title} with voice profile: {voiceProfileId}")
        
        # Validate voice profile
        if voiceProfileId not in VOICE_PROFILES:
            raise HTTPException(status_code=400, detail="Invalid voice profile ID")
        
        profile = VOICE_PROFILES[voiceProfileId]
        
        # Generate unique job ID
        job_id = str(uuid.uuid4())[:8]
        job_dir = OUTPUT_DIR / job_id
        job_dir.mkdir(exist_ok=True)
        
        # Save uploaded song
        song_path = job_dir / f"input_{song.filename}"
        
        async with aiofiles.open(song_path, "wb") as f:
            content = await song.read()
            await f.write(content)
        
        logger.info(f"Song saved: {song_path}")
        
        # Step 1: Separate vocals
        logger.info("Step 1: Separating vocals...")
        vocal_path, instrumental_path = separate_vocals(song_path)
        
        # Step 2: Convert voice
        logger.info("Step 2: Converting voice...")
        converted_vocal_path = convert_voice(
            vocal_path,
            voice_profile_id=voiceProfileId,
            method=profile.get("method", "basic")
        )
        
        # Step 3: Mix tracks
        logger.info("Step 3: Mixing tracks...")
        final_path = mix_tracks(converted_vocal_path, instrumental_path, job_dir)
        
        # Generate output filename
        output_filename = f"{job_id}_{title.replace(' ', '_')}.mp3"
        final_output = OUTPUT_DIR / output_filename
        
        # Move final file
        if final_path != final_output:
            final_path.rename(final_output)
        
        # Generate URL
        audio_url = f"/outputs/{output_filename}"
        
        logger.info(f"Processing complete: {audio_url}")
        
        return {
            "audioUrl": audio_url,
            "jobId": job_id,
            "message": "Song processed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing song: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """
    Get status of a processing job
    
    Args:
        job_id: Job ID
        
    Returns:
        JSON with job status
    """
    try:
        job_dir = OUTPUT_DIR / job_id
        
        if not job_dir.exists():
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Check if output file exists
        output_files = list(job_dir.glob("*.mp3"))
        
        if output_files:
            return {
                "status": "completed",
                "jobId": job_id,
                "audioUrl": f"/outputs/{output_files[0].name}"
            }
        else:
            return {
                "status": "processing",
                "jobId": job_id
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/profiles")
async def get_voice_profiles():
    """
    Get available voice profiles
    
    Returns:
        List of voice profiles
    """
    try:
        profiles = [
            {
                "id": profile_id,
                "name": profile.get("name", profile_id),
                "method": profile.get("method", "basic")
            }
            for profile_id, profile in VOICE_PROFILES.items()
        ]
        
        return {
            "profiles": profiles,
            "total": len(profiles)
        }
        
    except Exception as e:
        logger.error(f"Error getting profiles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/profiles/{profile_id}/delete")
async def delete_voice_profile(profile_id: str):
    """
    Delete a voice profile
    
    Args:
        profile_id: Profile ID to delete
        
    Returns:
        JSON with success message
    """
    try:
        if profile_id not in VOICE_PROFILES:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        if profile_id == "default":
            raise HTTPException(status_code=400, detail="Cannot delete default profile")
        
        del VOICE_PROFILES[profile_id]
        
        return {
            "message": f"Profile {profile_id} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Voice Clone Singer API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "upload_voice": "POST /voice",
            "process_song": "POST /process",
            "get_status": "GET /status/{job_id}",
            "get_profiles": "GET /profiles",
            "delete_profile": "POST /profiles/{profile_id}/delete"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 7860))
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
