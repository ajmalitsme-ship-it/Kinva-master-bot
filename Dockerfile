# Kinva Master - Dockerfile
FROM python:3.11-slim

# Install system dependencies (FFmpeg for video processing)

# Set working directory
WORKDIR /app

# Copy requirements first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

Run python auto_alive.py
# Create directories
RUN mkdir -p uploads outputs temp data logs static templates

# Expose ports
EXPOSE 8000 8080

Run python auto_error_fixer.py

# Run the app
CMD ["python", "kinva_master.py"]
