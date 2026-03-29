"""
Ultimate Vocal Remover (UVR) - Vocal Separation Module
Separates vocals from instrumental in audio files
"""

import subprocess
import logging
from pathlib import Path
from typing import Tuple
import numpy as np
import librosa
import soundfile as sf

logger = logging.getLogger(__name__)


def separate_vocals(song_path: Path) -> Tuple[Path, Path]:
    """
    Separate vocals from instrumental using librosa and scipy
    
    Args:
        song_path: Path to the input audio file
        
    Returns:
        Tuple of (vocal_path, instrumental_path)
    """
    try:
        logger.info(f"Separating vocals from: {song_path}")
        
        # Load audio
        y, sr = librosa.load(str(song_path), sr=None, mono=False)
        
        # Convert to mono if stereo
        if len(y.shape) > 1:
            y = np.mean(y, axis=0)
        
        # Simple vocal/instrumental separation using spectral analysis
        # This is a basic implementation - for production use Spleeter or similar
        D = librosa.stft(y)
        S = np.abs(D)
        
        # Create a simple mask (vocals typically have more energy in mid frequencies)
        # This is a placeholder - real UVR uses ML models
        freq_bins = S.shape[0]
        vocal_mask = np.ones_like(S)
        
        # Attenuate low frequencies (bass/drums) for vocal extraction
        low_freq_bins = int(freq_bins * 0.1)
        vocal_mask[:low_freq_bins] *= 0.3
        
        # Extract vocals and instrumental
        vocal_D = D * vocal_mask
        instrumental_D = D * (1 - vocal_mask * 0.7)
        
        # Inverse STFT
        vocal = librosa.istft(vocal_D)
        instrumental = librosa.istft(instrumental_D)
        
        # Normalize
        vocal = vocal / np.max(np.abs(vocal)) * 0.95
        instrumental = instrumental / np.max(np.abs(instrumental)) * 0.95
        
        # Save files
        vocal_path = Path(song_path.parent) / f"{song_path.stem}_vocal.wav"
        instrumental_path = Path(song_path.parent) / f"{song_path.stem}_instrumental.wav"
        
        sf.write(str(vocal_path), vocal, sr)
        sf.write(str(instrumental_path), instrumental, sr)
        
        logger.info(f"Vocal saved to: {vocal_path}")
        logger.info(f"Instrumental saved to: {instrumental_path}")
        
        return vocal_path, instrumental_path
        
    except Exception as e:
        logger.error(f"Error separating vocals: {str(e)}")
        raise


def separate_vocals_advanced(song_path: Path, model_path: str = None) -> Tuple[Path, Path]:
    """
    Advanced vocal separation using external tools (if available)
    Falls back to basic separation if tools not available
    
    Args:
        song_path: Path to the input audio file
        model_path: Optional path to UVR model
        
    Returns:
        Tuple of (vocal_path, instrumental_path)
    """
    try:
        # Try using demucs if available
        try:
            result = subprocess.run(
                ["demucs", "-n", "mdx_extra", "-o", str(song_path.parent), str(song_path)],
                capture_output=True,
                timeout=300
            )
            
            if result.returncode == 0:
                # Demucs creates separate files
                stem_dir = song_path.parent / "separated" / "mdx_extra" / song_path.stem
                vocal_path = stem_dir / "vocals.wav"
                instrumental_path = stem_dir / "no_vocals.wav"
                
                if vocal_path.exists() and instrumental_path.exists():
                    logger.info("Used Demucs for vocal separation")
                    return vocal_path, instrumental_path
        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning("Demucs not available, using basic separation")
        
        # Fall back to basic separation
        return separate_vocals(song_path)
        
    except Exception as e:
        logger.error(f"Error in advanced separation: {str(e)}")
        # Fall back to basic separation
        return separate_vocals(song_path)
