---
title: Voice Clone Singer Backend
emoji: 🎤
colorFrom: purple
colorTo: pink
sdk: docker
app_file: app.py
pinned: false
---

# Voice Clone Singer Backend

FastAPI-based backend server for voice conversion in songs. Separates vocals, converts voice, and mixes tracks back together.

## Features

- **Vocal Separation**: Extracts vocals and instrumental from songs using spectral analysis
- **Voice Conversion**: Converts vocals to target voice using basic pitch/formant shifting or RVC models
- **Audio Mixing**: Combines converted vocals with instrumental using FFmpeg or numpy
- **REST API**: FastAPI endpoints for voice upload, song processing, and status tracking
- **Static File Serving**: Serves converted audio files for download

## Architecture

```
voice-backend/
├── main.py              # FastAPI application
├── uvr_infer.py         # Vocal separation module
├── rvc_infer.py         # Voice conversion module
├── mix.py               # Audio mixing module
├── requirements.txt     # Python dependencies
├── uploads/             # Uploaded files
├── outputs/             # Processed audio files
└── models/              # RVC/UVR models (optional)
```

## Installation

### Prerequisites

- Python 3.8+
- FFmpeg (optional, for MP3 encoding)
- CUDA/GPU (optional, for faster processing)

### Setup

1. **Clone or create the backend directory**

```bash
cd voice-backend
```

2. **Create virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Install FFmpeg (optional but recommended)**

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
choco install ffmpeg
```

5. **Configure environment**

```bash
cp .env.example .env
# Edit .env and add your API keys if needed
```

## Running the Server

### Development

```bash
python main.py
```

The server will start on `http://localhost:7860`

### Production

```bash
uvicorn main:app --host 0.0.0.0 --port 7860 --workers 4
```

### Using Docker

```bash
docker build -t voice-clone-backend .
docker run -p 7860:7860 voice-clone-backend
```

## API Endpoints

### Health Check

```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-03-02T10:00:00"
}
```

### Upload Voice Sample

```bash
POST /voice
Content-Type: multipart/form-data

file: <audio_file>
```

Response:
```json
{
  "voiceProfileId": "abc12345",
  "message": "Voice sample uploaded successfully"
}
```

### Process Song

```bash
POST /process
Content-Type: multipart/form-data

song: <audio_file>
voiceProfileId: abc12345
title: My Song
```

Response:
```json
{
  "audioUrl": "/outputs/abc12345_My_Song.mp3",
  "jobId": "job123",
  "message": "Song processed successfully"
}
```

### Get Job Status

```bash
GET /status/{job_id}
```

Response:
```json
{
  "status": "completed",
  "jobId": "job123",
  "audioUrl": "/outputs/abc12345_My_Song.mp3"
}
```

### Get Voice Profiles

```bash
GET /profiles
```

Response:
```json
{
  "profiles": [
    {
      "id": "default",
      "name": "Default Voice",
      "method": "basic"
    }
  ],
  "total": 1
}
```

### Delete Voice Profile

```bash
POST /profiles/{profile_id}/delete
```

Response:
```json
{
  "message": "Profile abc12345 deleted successfully"
}
```

## Audio Processing Pipeline

### 1. Vocal Separation (UVR)

Extracts vocals from the input song using spectral analysis. The module:
- Loads audio file
- Performs STFT (Short-Time Fourier Transform)
- Creates masks for vocal/instrumental frequencies
- Applies inverse STFT to separate tracks

**Output**: `vocal.wav` and `instrumental.wav`

### 2. Voice Conversion (RVC)

Converts the vocal track to the target voice. Supports:
- **Basic**: Pitch shifting + formant modification
- **RVC**: Retrieval-based Voice Conversion (requires model files)
- **ElevenLabs**: API-based voice conversion (requires API key)

**Output**: `converted_vocal.wav`

### 3. Audio Mixing

Combines converted vocals with instrumental track:
- Normalizes audio levels
- Mixes tracks with configurable ratios (default: 70% vocal, 30% instrumental)
- Encodes to MP3 format

**Output**: `output.mp3`

## Configuration

### Environment Variables

```bash
# Server
HOST=0.0.0.0
PORT=7860

# ElevenLabs API (optional)
ELEVENLABS_API_KEY=your_key_here

# Logging
LOG_LEVEL=INFO
```

### Audio Processing Settings

Edit `main.py` to adjust:
- Vocal/instrumental mix ratio
- Audio quality/bitrate
- Processing timeouts
- Sample rates

## Advanced Setup

### Using RVC Models

1. Download RVC model files (`.pth` and `.index`)
2. Place in `models/rvc/` directory
3. Update voice profile configuration in `main.py`

### Using ElevenLabs API

1. Get API key from [elevenlabs.io](https://elevenlabs.io)
2. Set `ELEVENLABS_API_KEY` environment variable
3. Update voice profile to use `method: "elevenlabs"`

### Using Demucs for Better Separation

```bash
pip install demucs
```

The system will automatically use Demucs if available, otherwise falls back to librosa.

## Troubleshooting

### FFmpeg Not Found

Install FFmpeg or the system will use numpy-based mixing (slower but works).

### Out of Memory

Reduce audio quality or process shorter songs. Consider using GPU acceleration with PyTorch.

### Slow Processing

- Use GPU: `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118`
- Use Demucs for faster separation
- Increase server resources

### API Errors

Check logs for detailed error messages:
```bash
tail -f logs/app.log
```

## Integration with Frontend

### Frontend Configuration

Set the backend URL in `lib/api.ts`:

```typescript
export const BASE_URL = 'http://your-backend-url:7860';
```

### CORS

The backend allows CORS from all origins. In production, restrict to your frontend domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Performance

- **Vocal Separation**: 30-60 seconds (3-minute song)
- **Voice Conversion**: 10-30 seconds (3-minute song)
- **Audio Mixing**: 5-10 seconds
- **Total**: 45-100 seconds per song

Processing time depends on:
- Audio length
- Server hardware
- Processing method (basic vs RVC)
- GPU availability

## Deployment

### Local Development

```bash
python main.py
```

### Docker

```bash
docker build -t voice-clone-backend .
docker run -p 7860:7860 -v $(pwd)/uploads:/app/uploads -v $(pwd)/outputs:/app/outputs voice-clone-backend
```

### Cloud Deployment

#### RunPod

1. Create RunPod GPU pod
2. Upload backend files
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `python main.py`
5. Note the public URL

#### HuggingFace Spaces

1. Create new Space
2. Upload files
3. Create `app.py` that imports and runs FastAPI
4. HuggingFace will expose the URL

#### AWS/GCP/Azure

Use standard FastAPI deployment guides with GPU instances.

## License

MIT License

## Support

For issues or questions, check the logs and ensure:
- All dependencies are installed
- FFmpeg is available (optional)
- Backend is running on correct port
- Frontend is configured with correct backend URL
