# Space Station Cargo Management System

## Overview

The Space Station Cargo Management System is an intelligent stowage advisor designed to help astronauts efficiently manage cargo and storage on a space station. This system optimizes the placement, retrieval, and management of items within the limited space available in a microgravity environment.

## Core Features

- **Efficient Placement**: Suggests optimal locations for new cargo based on space availability, item priority, and accessibility constraints.
- **Quick Retrieval**: Recommends items that can be retrieved with minimal effort, considering factors like expiration dates and usage limits.
- **Rearrangement Optimization**: Provides suggestions for reorganizing items when space is limited or new shipments arrive.
- **Waste Management**: Automatically identifies and tracks items that have expired or reached their usage limit, suggesting appropriate waste disposal containers.
- **Cargo Return Planning**: Generates plans for waste return and space reclamation before resupply modules undock.
- **Comprehensive Logging**: Records all actions performed by astronauts for tracking and analysis.

## Technical Architecture

The system is built using Flask, a lightweight Python web framework, with SQLAlchemy for database management. The application follows a modular design with separate components for:

- **Web Interface**: User-friendly dashboard for astronauts to interact with the system
- **API Layer**: RESTful endpoints for programmatic access to the system
- **Optimization Algorithms**: Specialized algorithms for space optimization and retrieval planning
- **Database Models**: Structured data models for items, containers, placements, and logs

## Models

### Item
Represents cargo items with properties such as dimensions, mass, priority, expiry date, and usage limits.

### Container
Represents storage containers with defined zones and dimensions.

### ItemPlacement
Tracks the exact position and orientation of items within containers, including coordinates and rotation information.

### Log
Records all actions performed in the system, including placements, retrievals, and waste management activities.

## Installation

### Prerequisites
- Python 3.8+
- Docker (optional, for containerized deployment)

### Local Setup

1. Clone the repository:
   ```
   git clone https://github.com/your-username/space-station-cargo-management.git
   cd space-station-cargo-management
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables (optional):
   ```
   export DATABASE_URL="sqlite:///cargo_management.db"
   export SESSION_SECRET="your_secret_key"
   ```

4. Run the application:
   ```
   python main.py
   ```

### Docker Deployment

1. Build the Docker image:
   ```
   docker build -t space-station-cargo-management .
   ```

2. Run the container:
   ```
   docker run -p 5000:5000 space-station-cargo-management
   ```

## Usage

### Web Interface

Access the web interface by navigating to `http://localhost:5000` in your browser. The dashboard provides access to:

- **Dashboard**: Overview of current storage status and recommendations
- **Items**: Manage and track all cargo items
- **Containers**: View and configure storage containers
- **Simulation**: Test different storage scenarios
- **Logs**: Review history of all actions

### API Endpoints

The system provides RESTful API endpoints for programmatic access:

- `GET /api/items`: List all items
- `POST /api/items`: Create a new item
- `GET /api/containers`: List all containers
- `POST /api/containers`: Create a new container
- `GET /api/placements`: Get current item placements
- `POST /api/placements`: Create a new item placement
- `GET /api/recommendations`: Get storage recommendations

## Optimization Algorithms

The system employs several specialized algorithms:

- **Space Optimizer**: Determines the most efficient placement of items in containers
- **Retrieval Optimizer**: Calculates the optimal retrieval sequence for items
- **Waste Manager**: Identifies and manages items that should be marked as waste

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- This project was developed as part of the Space Station Cargo Management challenge.
- Special thanks to all contributors and testers who helped improve the system.
