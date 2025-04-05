import os
import logging
import sys
from app import app

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Default to port 5000 for Replit workflow
    # Use PORT environment variable if set (for Docker)
    # Use explicit port 8000 if running in Docker (check if in Docker environment)
    in_docker = os.path.exists('/.dockerenv')
    default_port = 8000 if in_docker else 5000
    port = int(os.environ.get("PORT", default_port))
    
    logger.info(f"Starting Space Station Cargo Management System on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
