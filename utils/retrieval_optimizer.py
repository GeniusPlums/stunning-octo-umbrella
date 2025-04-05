from typing import List, Dict, Tuple, Optional
import numpy as np
import logging
from datetime import datetime
from models import Item, Container, ItemPlacement

logger = logging.getLogger(__name__)

class RetrievalOptimizer:
    """
    Class responsible for optimizing item retrieval from containers
    based on priority, accessibility, and expiry dates
    """
    
    def __init__(self):
        pass
    
    def find_optimal_item_to_retrieve(self, item_name: str, items: List[Item], 
                                     containers: List[Container],
                                     placements: List[ItemPlacement]) -> Optional[Dict]:
        """
        Find the optimal item to retrieve based on name search
        Returns the item and retrieval instructions
        """
        logger.info(f"Finding optimal item to retrieve: {item_name}")
        
        # Find all matching items by name
        matching_items = [item for item in items if item_name.lower() in item.name.lower() and not item.is_waste]
        
        if not matching_items:
            logger.warning(f"No items found matching: {item_name}")
            return None
        
        # Get all placements for these items
        item_ids = [item.id for item in matching_items]
        matching_placements = [p for p in placements if p.item_id in item_ids]
        
        if not matching_placements:
            logger.warning(f"No placements found for items matching: {item_name}")
            return None
        
        best_item = None
        best_placement = None
        best_score = float('inf')
        retrieval_steps = []
        
        for item in matching_items:
            # Find all placements for this item
            item_placements = [p for p in placements if p.item_id == item.id]
            
            for placement in item_placements:
                # Find container for this placement
                container = next((c for c in containers if c.id == placement.container_id), None)
                if not container:
                    continue
                
                # Calculate retrieval complexity score (lower is better)
                retrieval_score, steps = self.calculate_retrieval_complexity(
                    item, placement, container, items, placements
                )
                
                # Add expiry factor - prioritize items closer to expiry
                expiry_factor = 0
                if item.expiry_date:
                    days_until_expiry = (item.expiry_date - datetime.now()).days
                    if days_until_expiry > 0:
                        # Prioritize items closer to expiry but not expired
                        expiry_factor = max(0, 100 - days_until_expiry) * 0.5
                
                # Calculate combined score (lower is better)
                # Weight factors: retrieval complexity, item priority, expiry
                combined_score = retrieval_score - (item.priority * 0.5) - expiry_factor
                
                if combined_score < best_score:
                    best_score = combined_score
                    best_item = item
                    best_placement = placement
                    retrieval_steps = steps
        
        if not best_item or not best_placement:
            return None
        
        # Get container for the best placement
        container = next((c for c in containers if c.id == best_placement.container_id), None)
        
        return {
            "item": best_item.to_dict(),
            "placement": best_placement.to_dict(),
            "container": container.to_dict() if container else None,
            "retrievalSteps": retrieval_steps,
            "stepsRequired": len(retrieval_steps)
        }
    
    def calculate_retrieval_complexity(self, target_item: Item, target_placement: ItemPlacement,
                                     container: Container, all_items: List[Item],
                                     all_placements: List[ItemPlacement]) -> Tuple[float, List[Dict]]:
        """
        Calculate how complex it is to retrieve an item
        Returns a complexity score and the steps needed
        """
        # Get all placements in this container
        container_placements = [p for p in all_placements if p.container_id == container.id]
        
        # Check if the item is directly accessible (visible from open face)
        is_visible = self.is_item_visible(target_placement, container, container_placements)
        
        if is_visible:
            # Item is directly accessible
            return 0.0, []
        
        # Item is blocked, need to identify blocking items
        blocking_items = self.find_blocking_items(
            target_placement, container, container_placements, all_items
        )
        
        # Generate steps for retrieval
        steps = []
        step_number = 1
        
        for blocking_placement, blocking_item in blocking_items:
            # Step to remove blocking item
            steps.append({
                "step": step_number,
                "action": "remove",
                "itemId": blocking_item.id,
                "containerId": container.id,
                "position": blocking_placement.to_dict()["position"]
            })
            step_number += 1
        
        # Step to remove target item
        steps.append({
            "step": step_number,
            "action": "retrieve",
            "itemId": target_item.id,
            "containerId": container.id,
            "position": target_placement.to_dict()["position"]
        })
        step_number += 1
        
        # Steps to put back blocking items
        for blocking_placement, blocking_item in reversed(blocking_items):
            steps.append({
                "step": step_number,
                "action": "place",
                "itemId": blocking_item.id,
                "containerId": container.id,
                "position": blocking_placement.to_dict()["position"]
            })
            step_number += 1
        
        # Complexity score is based on number of items to move and their mass
        complexity_score = len(blocking_items) * 10.0
        
        # Add mass factor - heavier items are harder to move
        for _, item in blocking_items:
            complexity_score += item.mass * 0.5
        
        return complexity_score, steps
    
    def is_item_visible(self, placement: ItemPlacement, container: Container, 
                      container_placements: List[ItemPlacement]) -> bool:
        """
        Check if an item is visible from the open face of the container
        """
        # An item is visible if it touches the open face (depth = 0)
        return placement.start_depth == 0
    
    def find_blocking_items(self, target_placement: ItemPlacement, container: Container,
                          container_placements: List[ItemPlacement], all_items: List[Item]) -> List[Tuple]:
        """
        Find items that block access to the target item
        Returns list of (placement, item) tuples sorted by retrieval order
        """
        # Items that block are those that are in front of the target item
        # (lower depth values in the same width/height ranges)
        blocking_placements = []
        
        target_start_w = target_placement.start_width
        target_end_w = target_placement.end_width
        target_start_h = target_placement.start_height
        target_end_h = target_placement.end_height
        target_start_d = target_placement.start_depth
        
        for placement in container_placements:
            # Skip if it's the target placement
            if placement.id == target_placement.id:
                continue
            
            # Check if this placement is in front of the target
            if (placement.end_depth <= target_start_d and  # In front of target (lower depth)
                # Overlaps in width
                ((placement.start_width < target_end_w and placement.end_width > target_start_w) or
                 (target_start_w < placement.end_width and target_end_w > placement.start_width)) and
                # Overlaps in height
                ((placement.start_height < target_end_h and placement.end_height > target_start_h) or
                 (target_start_h < placement.end_height and target_end_h > placement.start_height))):
                
                # Find the item for this placement
                blocking_item = next((item for item in all_items if item.id == placement.item_id), None)
                if blocking_item:
                    blocking_placements.append((placement, blocking_item))
        
        # Sort by depth (those furthest from open face should be removed first)
        blocking_placements.sort(key=lambda x: -x[0].start_depth)
        
        return blocking_placements
