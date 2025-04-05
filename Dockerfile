# Use Ubuntu 22.04 as the base image as required
FROM ubuntu:22.04

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml /app/
RUN pip3 install --no-cache-dir uv && \
    uv pip install --system -e .

# Copy project files
COPY . /app/

# Expose port 8000 for API access
EXPOSE 8000

# Run the application
CMD ["python3", "main.py"]
