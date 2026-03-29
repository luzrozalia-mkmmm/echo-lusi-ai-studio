"""
HuggingFace Spaces wrapper for Voice Clone Singer Backend
This file is used by HuggingFace Spaces to run the FastAPI application
"""

import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from main import app

# HuggingFace Spaces will run this file
# The app object is the FastAPI application

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment (HuggingFace sets this)
    port = int(os.getenv("PORT", 7860))
    host = "0.0.0.0"
    
    print(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
