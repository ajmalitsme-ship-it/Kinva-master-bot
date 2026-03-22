# ============================================
# KINVA MASTER - DOCKERFILE (Bullseye)
# ============================================

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY .auto_fix_ai.py

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# ============================================
# FIX: Create missing __init__.py files
# ============================================
RUN mkdir -p src/utils && \
    echo "from .helpers import allowed_file, format_size, get_file_info" > src/utils/__init__.py && \
    echo "" >> src/utils/__init__.py && \
    echo "__all__ = ['allowed_file', 'format_size', 'get_file_info']" >> src/utils/__init__.py && \
    echo '__version__ = "1.0.0"' > src/__init__.py && \
    touch src/handlers/__init__.py && \
    touch src/processors/__init__.py && \
    touch src/editors/__init__.py && \
    touch src/payment/__init__.py && \
    touch src/api/__init__.py

RUN mkdir -p uploads outputs logs data fonts

EXPOSE 5000

CMD ["gunicorn", "src.app:app", "--bind", "0.0.0.0:5000", "--workers", "4", "--threads", "2", "--timeout", "120"]
