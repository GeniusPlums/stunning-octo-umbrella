import os
import logging
from app import app

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting Space Station Cargo Management System on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
