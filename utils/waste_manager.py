from typing import List, Dict, Tuple, Optional
import logging
from datetime import datetime
from models import Item, Container, ItemPlacement

logger = logging.getLogger(__name__)

class WasteManager:
    """
    Class responsible for tracking waste items and planning cargo returns
    """
    
    def __init__(self):
        pass
    
    def identify_waste_items(self, items: List[Item], current_date: datetime = None) -> List[Item]:
        """
        Identify items that should be marked as waste (expired or used up)
        """
        if current_date is None:
            current_date = datetime.now()
        
        waste_items = []
        
        for item in items:
            # Skip items already marked as waste
            if item.is_waste:
                waste_items.append(item)
                continue
            
            # Check expiry date
            if item.expiry_date and item.expiry_date <= current_date:
                waste_items.append(item)
                continue
            
            # Check usage limit
            if item.remaining_uses <= 0:
                waste_items.append(item)
                continue
        
        return waste_items
    
    def plan_waste_disposal(self, waste_items: List[Item], undocking_container: Container,
                          current_placements: List[ItemPlacement], 
                          weight_limit: float = None) -> Dict:
        """
        Plan the disposal of waste items for undocking
        Returns disposal plan with instructions
        """
        logger.info(f"Planning waste disposal for {len(waste_items)} items")
        
        # Get current waste items in the undocking container
        undocking_items = []
        for placement in current_placements:
            if placement.container_id == undocking_container.id:
                item = next((i for i in waste_items if i.id == placement.item_id), None)
                if item:
                    undocking_items.append((item, placement))
        
        # Calculate current weight in undocking container
        current_weight = sum(item.mass for item, _ in undocking_items)
        
        # Determine remaining capacity
        remaining_capacity = float('inf')
        if weight_limit:
            remaining_capacity = weight_limit - current_weight
        
        # Sort waste items by priority (lower priority first) and then by mass
        # to maximize value of what gets loaded into undocking container
        sorted_waste = sorted(
            waste_items, 
            key=lambda x: (x.priority, -x.mass)
        )
        
        # Items to move to undocking container
        items_to_move = []
        
        for item in sorted_waste:
            # Skip items already in undocking container
            if any(existing[0].id == item.id for existing in undocking_items):
                continue
            
            # Check if we have capacity
            if item.mass <= remaining_capacity:
                items_to_move.append(item)
                remaining_capacity -= item.mass
        
        # Generate disposal plan
        steps = []
        step_number = 1
        manifest = []
        
        # Steps for moving items to undocking container
        for item in items_to_move:
            # Find current placement for this item
            current_placement = next(
                (p for p in current_placements if p.item_id == item.id and p.container_id != undocking_container.id),
                None
            )
            
            if current_placement:
                # Add step to remove from current container
                steps.append({
                    "step": step_number,
                    "action": "remove",
                    "itemId": item.id,
                    "fromContainer": current_placement.container_id,
                    "fromPosition": {
                        "startCoordinates": {
                            "width": current_placement.start_width,
                            "depth": current_placement.start_depth,
                            "height": current_placement.start_height
                        },
                        "endCoordinates": {
                            "width": current_placement.end_width,
                            "depth": current_placement.end_depth,
                            "height": current_placement.end_height
                        }
                    }
                })
                step_number += 1
                
                # Add step to place in undocking container
                # For simplicity, we're not calculating exact position
                steps.append({
                    "step": step_number,
                    "action": "place",
                    "itemId": item.id,
                    "toContainer": undocking_container.id,
                    "toPosition": {
                        "startCoordinates": {"width": 0, "depth": 0, "height": 0},
                        "endCoordinates": {
                            "width": item.width, "depth": item.depth, "height": item.height
                        }
                    }
                })
                step_number += 1
                
                # Add to manifest
                manifest.append({
                    "itemId": item.id,
                    "name": item.name,
                    "mass": item.mass
                })
        
        # Add existing items to manifest
        for item, _ in undocking_items:
            manifest.append({
                "itemId": item.id,
                "name": item.name,
                "mass": item.mass
            })
        
        # Calculate total mass
        total_mass = sum(item.mass for item in items_to_move) + current_weight
        
        return {
            "undockingContainer": undocking_container.id,
            "totalItems": len(manifest),
            "totalMass": total_mass,
            "remainingCapacity": remaining_capacity if weight_limit else None,
            "manifest": manifest,
            "disposalSteps": steps
        }
    
    def simulate_time_advancement(self, items: List[Item], days: int = 1) -> Dict:
        """
        Simulate the advancement of time by a number of days
        Returns changes in item statuses
        """
        if days <= 0:
            return {"success": False, "message": "Days must be greater than 0"}
        
        current_date = datetime.now()
        new_date = current_date.replace(day=current_date.day + days)
        
        changes = {
            "date": {
                "from": current_date.isoformat(),
                "to": new_date.isoformat()
            },
            "expiredItems": [],
            "usedUpItems": []
        }
        
        # Check for items that will expire
        for item in items:
            if item.is_waste:
                continue
                
            if item.expiry_date and item.expiry_date <= new_date and item.expiry_date > current_date:
                changes["expiredItems"].append({
                    "itemId": item.id,
                    "name": item.name,
                    "expiryDate": item.expiry_date.isoformat()
                })
        
        return {
            "success": True,
            "changes": changes,
            "newWasteItems": len(changes["expiredItems"]) + len(changes["usedUpItems"])
        }
