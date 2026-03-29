"""
Audio Mixing Module
Combines converted vocals with instrumental using FFmpeg
"""

import subprocess
import logging
from pathlib import Path
import numpy as np
import librosa
import soundfile as sf

logger = logging.getLogger(__name__)


def mix_tracks_ffmpeg(vocal: Path, instrumental: Path, output_dir: Path) -> Path:
    """
    Mix vocal and instrumental tracks using FFmpeg
    
    Args:
        vocal: Path to vocal audio file
        instrumental: Path to instrumental audio file
        output_dir: Directory to save output file
        
    Returns:
        Path to mixed audio file
    """
    try:
        logger.info(f"Mixing tracks using FFmpeg")
        logger.info(f"Vocal: {vocal}")
        logger.info(f"Instrumental: {instrumental}")
        
        output_path = output_dir / "output.mp3"
        
        # FFmpeg command to mix audio tracks
        # Use filter_complex to mix the two audio streams
        cmd = [
            "ffmpeg",
            "-i", str(vocal),
            "-i", str(instrumental),
            "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=longest[a]",
            "-map", "[a]",
            "-c:a", "libmp3lame",
            "-q:a", "4",
            "-y",  # Overwrite output file
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, timeout=300)
        
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr.decode()}")
            # Fall back to numpy mixing
            return mix_tracks_numpy(vocal, instrumental, output_dir)
        
        logger.info(f"Mixed audio saved to: {output_path}")
        return output_path
        
    except FileNotFoundError:
        logger.warning("FFmpeg not found, using numpy mixing")
        return mix_tracks_numpy(vocal, instrumental, output_dir)
    except Exception as e:
        logger.error(f"Error mixing with FFmpeg: {str(e)}")
        return mix_tracks_numpy(vocal, instrumental, output_dir)


def mix_tracks_numpy(vocal: Path, instrumental: Path, output_dir: Path) -> Path:
    """
    Mix vocal and instrumental tracks using numpy
    Fallback when FFmpeg is not available
    
    Args:
        vocal: Path to vocal audio file
        instrumental: Path to instrumental audio file
        output_dir: Directory to save output file
        
    Returns:
        Path to mixed audio file
    """
    try:
        logger.info("Mixing tracks using numpy")
        
        # Load audio files
        vocal_data, sr_vocal = librosa.load(str(vocal), sr=None)
        instrumental_data, sr_instrumental = librosa.load(str(instrumental), sr=None)
        
        # Ensure same sample rate
        if sr_vocal != sr_instrumental:
            logger.warning(f"Sample rate mismatch: vocal={sr_vocal}, instrumental={sr_instrumental}")
            # Resample to higher rate
            sr = max(sr_vocal, sr_instrumental)
            if sr_vocal != sr:
                vocal_data = librosa.resample(vocal_data, orig_sr=sr_vocal, target_sr=sr)
            if sr_instrumental != sr:
                instrumental_data = librosa.resample(instrumental_data, orig_sr=sr_instrumental, target_sr=sr)
        else:
            sr = sr_vocal
        
        # Ensure same length
        min_len = min(len(vocal_data), len(instrumental_data))
        vocal_data = vocal_data[:min_len]
        instrumental_data = instrumental_data[:min_len]
        
        # Mix tracks with vocal at 0.7 and instrumental at 0.3
        mixed = vocal_data * 0.7 + instrumental_data * 0.3
        
        # Normalize to prevent clipping
        max_val = np.max(np.abs(mixed))
        if max_val > 0:
            mixed = mixed / max_val * 0.95
        
        # Save as MP3
        output_path = output_dir / "output.mp3"
        
        # First save as WAV (for compatibility)
        wav_path = output_dir / "output.wav"
        sf.write(str(wav_path), mixed, sr)
        
        # Try to convert to MP3 using FFmpeg
        try:
            cmd = [
                "ffmpeg",
                "-i", str(wav_path),
                "-c:a", "libmp3lame",
                "-q:a", "4",
                "-y",
                str(output_path)
            ]
            subprocess.run(cmd, capture_output=True, timeout=60)
            
            # Remove temporary WAV file
            wav_path.unlink()
            logger.info(f"Mixed audio saved to: {output_path}")
            
        except Exception as e:
            logger.warning(f"Could not convert to MP3: {str(e)}, keeping WAV")
            output_path = wav_path
        
        return output_path
        
    except Exception as e:
        logger.error(f"Error mixing with numpy: {str(e)}")
        raise


def mix_tracks(vocal: Path, instrumental: Path, output_dir: Path) -> Path:
    """
    Main mixing function - tries FFmpeg first, falls back to numpy
    
    Args:
        vocal: Path to vocal audio file
        instrumental: Path to instrumental audio file
        output_dir: Directory to save output file
        
    Returns:
        Path to mixed audio file
    """
    try:
        # Try FFmpeg first
        return mix_tracks_ffmpeg(vocal, instrumental, output_dir)
    except Exception as e:
        logger.warning(f"FFmpeg mixing failed: {str(e)}, trying numpy")
        return mix_tracks_numpy(vocal, instrumental, output_dir)
