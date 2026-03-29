FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py .
COPY uvr_infer.py .
COPY rvc_infer.py .
COPY mix.py .

# Create directories
RUN mkdir -p uploads outputs models

# Expose port
EXPOSE 7860

# Run application
CMD ["python", "main.py"]
