# ============================================
# KINVA MASTER - DOCKERFILE (Bullseye)
# ============================================

# Base image with Debian Bullseye
FROM python:3.11-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies (for Bullseye)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1 \
    libglib2.0-0 \
    libxcb1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p uploads outputs logs data fonts static/css/themes static/js/lib static/images/{icons,backgrounds,templates}

# Run setup script
RUN chmod +x setup.sh && ./setup.sh || true

# Expose port
EXPOSE 5000

# Run application
CMD ["gunicorn", "src.app:app", "--bind", "0.0.0.0:5000", "--workers", "4", "--threads", "2", "--timeout", "120"]
