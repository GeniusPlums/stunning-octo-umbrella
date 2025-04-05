from flask import Flask, request, jsonify
import json
import logging
from datetime import datetime
import os
from typing import Dict, List, Optional

from app import db
from models import Item, Container, ItemPlacement, Log
from utils.space_optimizer import SpaceOptimizer
from utils.retrieval_optimizer import RetrievalOptimizer
from utils.waste_manager import WasteManager

logger = logging.getLogger(__name__)

# Initialize utility classes
space_optimizer = SpaceOptimizer()
retrieval_optimizer = RetrievalOptimizer()
waste_manager = WasteManager()

def register_api_routes(app: Flask):
    """Register all API routes with the Flask application"""
    
    @app.route('/api/placement', methods=['POST'])
    def placement_recommendations():
        """
        API to recommend placements for new items
        """
        try:
            data = request.json
            
            if not data or 'items' not in data or 'containers' not in data:
                return jsonify({"success": False, "message": "Invalid request data"}), 400
            
            # Process items from request
            items_data = data['items']
            items = []
            
            for item_data in items_data:
                # Convert expiry date string to datetime if it exists
                expiry_date = None
                if 'expiryDate' in item_data and item_data['expiryDate']:
                    try:
                        expiry_date = datetime.fromisoformat(item_data['expiryDate'])
                    except ValueError:
                        logger.warning(f"Invalid expiry date format: {item_data['expiryDate']}")
                
                # Create Item object
                item = Item(
                    id=item_data['itemId'],
                    name=item_data['name'],
                    width=item_data['width'],
                    depth=item_data['depth'],
                    height=item_data['height'],
                    mass=item_data.get('mass', 1.0),  # Default mass if not provided
                    priority=item_data['priority'],
                    expiry_date=expiry_date,
                    usage_limit=item_data.get('usageLimit', 1),
                    remaining_uses=item_data.get('usageLimit', 1),  # Default to full uses
                    preferred_zone=item_data.get('preferredZone')
                )
                items.append(item)
            
            # Process containers from request
            containers_data = data['containers']
            containers = []
            
            for container_data in containers_data:
                container = Container(
                    id=container_data['containerId'],
                    zone=container_data['zone'],
                    width=container_data['width'],
                    depth=container_data['depth'],
                    height=container_data['height']
                )
                containers.append(container)
            
            # Get existing placements from database
            existing_placements = {}
            for container in containers:
                container_placements = ItemPlacement.query.filter_by(container_id=container.id).all()
                existing_placements[container.id] = container_placements
            
            # Run optimization algorithm
            optimization_result = space_optimizer.optimize_placement_for_items(
                items, containers, existing_placements
            )
            
            # Save new items and placements to database if optimization succeeded
            if optimization_result['success']:
                for item in items:
                    # Check if item already exists
                    existing_item = Item.query.get(item.id)
                    if existing_item:
                        # Update existing item
                        existing_item.name = item.name
                        existing_item.width = item.width
                        existing_item.depth = item.depth
                        existing_item.height = item.height
                        existing_item.mass = item.mass
                        existing_item.priority = item.priority
                        existing_item.expiry_date = item.expiry_date
                        existing_item.usage_limit = item.usage_limit
                        existing_item.remaining_uses = item.remaining_uses
                        existing_item.preferred_zone = item.preferred_zone
                    else:
                        # Add new item
                        db.session.add(item)
                
                # Save placements
                for placement_data in optimization_result['placements']:
                    item_id = placement_data['itemId']
                    container_id = placement_data['containerId']
                    position = placement_data['position']
                    
                    # Create new placement
                    placement = ItemPlacement(
                        item_id=item_id,
                        container_id=container_id,
                        start_width=position['startCoordinates']['width'],
                        start_depth=position['startCoordinates']['depth'],
                        start_height=position['startCoordinates']['height'],
                        end_width=position['endCoordinates']['width'],
                        end_depth=position['endCoordinates']['depth'],
                        end_height=position['endCoordinates']['height']
                    )
                    
                    # Add rotation info if available
                    if 'rotation' in position:
                        placement.rotated_width_depth = position['rotation'].get('widthDepth', False)
                        placement.rotated_width_height = position['rotation'].get('widthHeight', False)
                        placement.rotated_depth_height = position['rotation'].get('depthHeight', False)
                    
                    db.session.add(placement)
                    
                    # Add log entry
                    log = Log(
                        action_type="placement",
                        item_id=item_id,
                        container_id=container_id,
                        details=f"Item placed in container {container_id}"
                    )
                    db.session.add(log)
                
                db.session.commit()
            
            return jsonify(optimization_result)
            
        except Exception as e:
            logger.exception("Error in placement recommendations")
            db.session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500
    
    @app.route('/api/search', methods=['GET'])
    def search_item():
        """
        API to search for an item and get retrieval instructions
        """
        try:
            item_name = request.args.get('name')
            astronaut_id = request.args.get('astronautId')
            
            if not item_name:
                return jsonify({"success": False, "message": "Item name is required"}), 400
            
            # Get all items, containers, and placements
            items = Item.query.filter(Item.is_waste == False).all()
            containers = Container.query.all()
            placements = ItemPlacement.query.all()
            
            # Find the optimal item to retrieve
            result = retrieval_optimizer.find_optimal_item_to_retrieve(
                item_name, items, containers, placements
            )
            
            if not result:
                return jsonify({"success": False, "message": "No matching items found"}), 404
            
            # Update item usage count if retrieval is successful
            item = Item.query.get(result['item']['itemId'])
            if item:
                item.remaining_uses -= 1
                
                # Check if item is now waste
                if item.should_be_waste():
                    item.is_waste = True
                
                # Add log entry
                log = Log(
                    action_type="retrieval",
                    item_id=item.id,
                    container_id=result['container']['containerId'],
                    astronaut_id=astronaut_id,
                    details=f"Item retrieved by {astronaut_id or 'unknown astronaut'}"
                )
                db.session.add(log)
                
                db.session.commit()
            
            return jsonify({
                "success": True,
                "item": result['item'],
                "container": result['container'],
                "retrievalSteps": result['retrievalSteps'],
                "stepsRequired": result['stepsRequired'],
                "isNowWaste": item.is_waste if item else False
            })
            
        except Exception as e:
            logger.exception("Error in item search")
            db.session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500
    
    @app.route('/api/waste/identify', methods=['GET'])
    def identify_waste():
        """
        API to identify waste items
        """
        try:
            # Get all items from database
            items = Item.query.all()
            
            # Identify waste items
            waste_items = waste_manager.identify_waste_items(items)
            
            # Update waste flag in database
            for item in waste_items:
                item.is_waste = True
            
            db.session.commit()
            
            return jsonify({
                "success": True,
                "wasteItems": [item.to_dict() for item in waste_items],
                "totalWaste": len(waste_items)
            })
            
        except Exception as e:
            logger.exception("Error identifying waste")
            db.session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500
    
    @app.route('/api/waste/disposal', methods=['POST'])
    def plan_waste_disposal():
        """
        API to plan waste disposal for undocking
        """
        try:
            data = request.json
            
            if not data or 'undockingContainerId' not in data:
                return jsonify({"success": False, "message": "Undocking container ID is required"}), 400
            
            undocking_container_id = data['undockingContainerId']
            weight_limit = data.get('weightLimit')
            
            # Get undocking container
            undocking_container = Container.query.get(undocking_container_id)
            if not undocking_container:
                return jsonify({"success": False, "message": "Undocking container not found"}), 404
            
            # Get waste items
            waste_items = Item.query.filter_by(is_waste=True).all()
            
            # Get current placements
            placements = ItemPlacement.query.all()
            
            # Plan waste disposal
            disposal_plan = waste_manager.plan_waste_disposal(
                waste_items, undocking_container, placements, weight_limit
            )
            
            return jsonify({
                "success": True,
                "disposalPlan": disposal_plan
            })
            
        except Exception as e:
            logger.exception("Error planning waste disposal")
            return jsonify({"success": False, "message": str(e)}), 500
    
    @app.route('/api/simulation/time', methods=['POST'])
    def simulate_time():
        """
        API to simulate advancement of time
        """
        try:
            data = request.json
            
            if not data or 'days' not in data:
                return jsonify({"success": False, "message": "Number of days is required"}), 400
            
            days = data['days']
            used_items = data.get('usedItems', [])
            
            # Get all items from database
            items = Item.query.all()
            
            # Mark used items
            for used_item_id in used_items:
                item = Item.query.get(used_item_id)
                if item:
                    item.remaining_uses -= 1
                    
                    # Check if item is now waste
                    if item.should_be_waste():
                        item.is_waste = True
            
            # Simulate time advancement
            simulation_result = waste_manager.simulate_time_advancement(items, days)
            
            if simulation_result['success']:
                # Update items that expired due to time advancement
                for expired_item_data in simulation_result['changes']['expiredItems']:
                    item = Item.query.get(expired_item_data['itemId'])
                    if item:
                        item.is_waste = True
                
                db.session.commit()
            
            return jsonify(simulation_result)
            
        except Exception as e:
            logger.exception("Error simulating time")
            db.session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500
    
    @app.route('/api/containers', methods=['GET'])
    def get_containers():
        """
        API to get all containers
        """
        try:
            containers = Container.query.all()
            return jsonify({
                "success": True,
                "containers": [container.to_dict() for container in containers]
            })
        except Exception as e:
            logger.exception("Error getting containers")
            return jsonify({"success": False, "message": str(e)}), 500
    
    @app.route('/api/items', methods=['GET'])
    def get_items():
        """
        API to get all items
        """
        try:
            items = Item.query.all()
            return jsonify({
                "success": True,
                "items": [item.to_dict() for item in items]
            })
        except Exception as e:
            logger.exception("Error getting items")
            return jsonify({"success": False, "message": str(e)}), 500
    
    @app.route('/api/logs', methods=['GET'])
    def get_logs():
        """
        API to get action logs
        """
        try:
            logs = Log.query.order_by(Log.timestamp.desc()).limit(100).all()
            return jsonify({
                "success": True,
                "logs": [log.to_dict() for log in logs]
            })
        except Exception as e:
            logger.exception("Error getting logs")
            return jsonify({"success": False, "message": str(e)}), 500
    
    @app.route('/api/undock', methods=['POST'])
    def perform_undock():
        """
        API to perform undocking operation
        """
        try:
            data = request.json
            
            if not data or 'containerId' not in data:
                return jsonify({"success": False, "message": "Container ID is required"}), 400
            
            container_id = data['containerId']
            
            # Get container
            container = Container.query.get(container_id)
            if not container:
                return jsonify({"success": False, "message": "Container not found"}), 404
            
            # Get all placements in this container
            placements = ItemPlacement.query.filter_by(container_id=container_id).all()
            
            # Get items in these placements
            item_ids = [placement.item_id for placement in placements]
            items = Item.query.filter(Item.id.in_(item_ids)).all()
            
            # Remove placements
            for placement in placements:
                db.session.delete(placement)
            
            # For waste items, remove them from inventory
            waste_items = [item for item in items if item.is_waste]
            for item in waste_items:
                db.session.delete(item)
            
            # Add log entry
            log = Log(
                action_type="undock",
                container_id=container_id,
                details=f"Container undocked with {len(waste_items)} waste items"
            )
            db.session.add(log)
            
            db.session.commit()
            
            return jsonify({
                "success": True,
                "containerId": container_id,
                "itemsRemoved": len(waste_items),
                "message": f"Container {container_id} undocked successfully with {len(waste_items)} waste items"
            })
            
        except Exception as e:
            logger.exception("Error performing undock")
            db.session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500
