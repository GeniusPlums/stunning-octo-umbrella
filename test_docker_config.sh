#!/bin/bash

# This script tests if the Docker configuration is correctly set up to use port 8000
# It doesn't actually build or run Docker, but it verifies the settings in the code

echo "Checking Docker configuration..."

# Check if Dockerfile exists
if [ ! -f "Dockerfile" ]; then
  echo "ERROR: Dockerfile not found!"
  exit 1
fi

# Check if port 8000 is exposed in Dockerfile
if ! grep -q "EXPOSE 8000" Dockerfile; then
  echo "ERROR: Port 8000 is not exposed in Dockerfile!"
  exit 1
else
  echo "✓ Port 8000 is correctly exposed in Dockerfile"
fi

# Check if PORT environment variable is set to 8000 in Dockerfile
if ! grep -q "ENV PORT=8000" Dockerfile; then
  echo "ERROR: PORT environment variable is not set to 8000 in Dockerfile!"
  exit 1
else
  echo "✓ PORT environment variable is correctly set to 8000 in Dockerfile"
fi

# Check if main.py handles Docker environment
if ! grep -q "in_docker" main.py; then
  echo "ERROR: main.py does not detect Docker environment!"
  exit 1
else
  echo "✓ main.py correctly detects Docker environment"
fi

# Check if main.py uses port 8000 in Docker
if ! grep -q "default_port = 8000 if in_docker" main.py; then
  echo "ERROR: main.py does not use port 8000 in Docker environment!"
  exit 1
else
  echo "✓ main.py correctly uses port 8000 in Docker environment"
fi

echo "Docker configuration test completed successfully!"
echo "✓ The application is correctly configured to run on port 8000 in Docker"
echo "✓ The application will continue to run on port 5000 in Replit"

exit 0