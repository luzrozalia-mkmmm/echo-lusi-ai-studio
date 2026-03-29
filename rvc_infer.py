"""
Voice Conversion Module
Supports both RVC (Retrieval-based Voice Conversion) and ElevenLabs API
"""

import logging
import os
import requests
from pathlib import Path
from typing import Optional
import numpy as np
import librosa
import soundfile as sf

logger = logging.getLogger(__name__)

# ElevenLabs API configuration
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1"


def convert_voice_elevenlabs(
    vocal_path: Path,
    voice_id: str = "default",
    stability: float = 0.5,
    similarity_boost: float = 0.75
) -> Path:
    """
    Convert voice using ElevenLabs API
    
    Args:
        vocal_path: Path to vocal audio file
        voice_id: ElevenLabs voice ID
        stability: Voice stability (0-1)
        similarity_boost: Similarity boost (0-1)
        
    Returns:
        Path to converted audio file
    """
    try:
        if not ELEVENLABS_API_KEY:
            logger.warning("ElevenLabs API key not set, using basic conversion")
            return convert_voice_basic(vocal_path)
        
        logger.info(f"Converting voice using ElevenLabs API with voice ID: {voice_id}")
        
        # Read audio file
        with open(vocal_path, "rb") as f:
            audio_data = f.read()
        
        # Call ElevenLabs API
        url = f"{ELEVENLABS_API_URL}/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "audio/mpeg"
        }
        
        # Note: ElevenLabs primarily does text-to-speech
        # For voice conversion, we'd need to use their voice cloning feature
        # This is a simplified example
        
        # For now, use basic conversion
        logger.info("ElevenLabs voice conversion requires voice cloning setup")
        return convert_voice_basic(vocal_path)
        
    except Exception as e:
        logger.error(f"Error in ElevenLabs conversion: {str(e)}")
        return convert_voice_basic(vocal_path)


def convert_voice_basic(vocal_path: Path) -> Path:
    """
    Basic voice conversion using pitch shifting and formant modification
    This is a placeholder - real RVC would use deep learning models
    
    Args:
        vocal_path: Path to vocal audio file
        
    Returns:
        Path to converted audio file
    """
    try:
        logger.info(f"Applying basic voice conversion to: {vocal_path}")
        
        # Load audio
        y, sr = librosa.load(str(vocal_path), sr=None)
        
        # Apply pitch shifting (simulate voice change)
        # In real RVC, this would use trained models
        pitch_shift = -3  # Shift down by 3 semitones (example)
        y_shifted = librosa.effects.pitch_shift(y, sr=sr, n_steps=pitch_shift)
        
        # Apply time stretching for formant modification
        time_stretch = 0.95
        y_stretched = librosa.effects.time_stretch(y_shifted, rate=time_stretch)
        
        # Apply slight EQ to simulate different voice characteristics
        # Boost mid frequencies
        D = librosa.stft(y_stretched)
        S = np.abs(D)
        
        # Create frequency-based filter
        freqs = librosa.fft_frequencies(sr=sr)
        mid_freq_mask = np.exp(-((freqs - 1000) ** 2) / (2 * 500 ** 2))
        mid_freq_mask = 1 + mid_freq_mask * 0.3  # Boost by 30%
        
        # Apply filter
        D_filtered = D * mid_freq_mask[:, np.newaxis]
        y_filtered = librosa.istft(D_filtered)
        
        # Normalize
        y_filtered = y_filtered / np.max(np.abs(y_filtered)) * 0.95
        
        # Save converted audio
        output_path = vocal_path.parent / f"{vocal_path.stem}_converted.wav"
        sf.write(str(output_path), y_filtered, sr)
        
        logger.info(f"Converted voice saved to: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error in basic voice conversion: {str(e)}")
        raise


def convert_voice_rvc(
    vocal_path: Path,
    model_path: str,
    index_path: Optional[str] = None,
    pitch_shift: int = 0
) -> Path:
    """
    Convert voice using RVC (Retrieval-based Voice Conversion)
    Requires RVC model files
    
    Args:
        vocal_path: Path to vocal audio file
        model_path: Path to RVC model (.pth file)
        index_path: Optional path to RVC index file
        pitch_shift: Pitch shift in semitones
        
    Returns:
        Path to converted audio file
    """
    try:
        logger.info(f"Converting voice using RVC model: {model_path}")
        
        if not Path(model_path).exists():
            logger.warning(f"RVC model not found: {model_path}, using basic conversion")
            return convert_voice_basic(vocal_path)
        
        # This is a placeholder for RVC integration
        # Real implementation would use RVC inference code
        # For now, use basic conversion
        logger.info("RVC model found, but full integration requires RVC library setup")
        return convert_voice_basic(vocal_path)
        
    except Exception as e:
        logger.error(f"Error in RVC conversion: {str(e)}")
        return convert_voice_basic(vocal_path)


def convert_voice(
    vocal_path: Path,
    voice_profile_id: str = "default",
    method: str = "basic"
) -> Path:
    """
    Main voice conversion function
    
    Args:
        vocal_path: Path to vocal audio file
        voice_profile_id: Voice profile identifier
        method: Conversion method ("basic", "elevenlabs", or "rvc")
        
    Returns:
        Path to converted audio file
    """
    if method == "elevenlabs":
        return convert_voice_elevenlabs(vocal_path, voice_id=voice_profile_id)
    elif method == "rvc":
        model_path = f"models/rvc/{voice_profile_id}.pth"
        index_path = f"models/rvc/{voice_profile_id}.index"
        return convert_voice_rvc(vocal_path, model_path, index_path)
    else:
        return convert_voice_basic(vocal_path)
