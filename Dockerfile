# WillGPT - Multi-Platform RAG System
# Base image with Python 3.13
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY parsers/ ./parsers/
COPY retrieval/ ./retrieval/
COPY notebooks/ ./notebooks/
COPY merge_and_upload.py .
COPY tests/test_parser.py .
COPY tests/test_qdrant_connection.py .

# Create data directories
RUN mkdir -p data/raw data/processed

# Set Python to run in unbuffered mode (better for logs)
ENV PYTHONUNBUFFERED=1

# Default command (can be overridden)
CMD ["/bin/bash"]
