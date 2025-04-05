import numpy as np
from typing import List, Dict, Tuple, Any, Optional
import logging
from models import Item, Container, ItemPlacement

logger = logging.getLogger(__name__)

class SpaceOptimizer:
    """
    Class responsible for optimizing placement of items in containers
    using 3D bin packing algorithms
    """
    
    def __init__(self):
        self.container_spaces = {}  # Cache of container space matrices
    
    def reset_container_space(self, container_id: str):
        """Remove container from cache to force recalculation"""
        if container_id in self.container_spaces:
            del self.container_spaces[container_id]
    
    def get_container_space_matrix(self, container: Container, placements: List[ItemPlacement]) -> np.ndarray:
        """
        Create or retrieve a 3D matrix representing the container's space
        1 means occupied, 0 means free
        """
        # Check if we have this in cache
        if container.id in self.container_spaces:
            return self.container_spaces[container.id]
        
        # Create a new space matrix with granularity of 1cm
        width = int(container.width)
        depth = int(container.depth)
        height = int(container.height)
        
        space_matrix = np.zeros((width, depth, height), dtype=np.int8)
        
        # Mark occupied spaces based on existing placements
        for placement in placements:
            start_w = int(placement.start_width)
            start_d = int(placement.start_depth)
            start_h = int(placement.start_height)
            end_w = int(placement.end_width)
            end_d = int(placement.end_depth)
            end_h = int(placement.end_height)
            
            # Mark as occupied
            space_matrix[start_w:end_w, start_d:end_d, start_h:end_h] = 1
        
        # Cache the result
        self.container_spaces[container.id] = space_matrix
        return space_matrix
    
    def find_placement_for_item(self, item: Item, container: Container, 
                               existing_placements: List[ItemPlacement]) -> Optional[Dict]:
        """
        Find the optimal placement for an item in a container
        Returns placement coordinates or None if placement is not possible
        """
        logger.debug(f"Finding placement for item {item.id} in container {container.id}")
        
        # Get current space utilization
        space_matrix = self.get_container_space_matrix(container, existing_placements)
        
        # Try all possible orientations of the item
        orientations = self.get_possible_orientations(item)
        
        best_placement = None
        best_accessibility_score = float('inf')
        
        for orientation in orientations:
            width, depth, height = orientation['dimensions']
            rotation = orientation['rotation']
            
            # Check if this orientation fits in the container
            if width > container.width or depth > container.depth or height > container.height:
                continue
            
            # Find possible placements with this orientation
            possible_placements = self.find_possible_positions(space_matrix, width, depth, height)
            
            for pos in possible_placements:
                start_w, start_d, start_h = pos
                
                # Calculate end coordinates
                end_w = start_w + width
                end_d = start_d + depth
                end_h = start_h + height
                
                # Calculate accessibility score (lower is better)
                # Based on depth (further from open face is worse) and items above
                accessibility_score = self.calculate_accessibility_score(
                    space_matrix, start_w, start_d, start_h, end_w, end_d, end_h
                )
                
                # Check if preferred zone matches
                zone_score = 0 if container.zone == item.preferred_zone else 10000
                
                # Combine scores
                total_score = accessibility_score + zone_score
                
                # Update best placement if this is better
                if best_placement is None or total_score < best_accessibility_score:
                    best_accessibility_score = total_score
                    best_placement = {
                        "startCoordinates": {"width": start_w, "depth": start_d, "height": start_h},
                        "endCoordinates": {"width": end_w, "depth": end_d, "height": end_h},
                        "rotation": rotation
                    }
        
        return best_placement
    
    def get_possible_orientations(self, item: Item) -> List[Dict]:
        """Return all possible orientations of the item (accounting for rotation)"""
        w, d, h = item.width, item.depth, item.height
        
        # All possible orientations
        orientations = [
            {"dimensions": (w, d, h), "rotation": {"widthDepth": False, "widthHeight": False, "depthHeight": False}},
            {"dimensions": (d, w, h), "rotation": {"widthDepth": True, "widthHeight": False, "depthHeight": False}},
            {"dimensions": (w, h, d), "rotation": {"widthDepth": False, "widthHeight": False, "depthHeight": True}},
            {"dimensions": (h, w, d), "rotation": {"widthDepth": False, "widthHeight": True, "depthHeight": True}},
            {"dimensions": (d, h, w), "rotation": {"widthDepth": True, "widthHeight": False, "depthHeight": True}},
            {"dimensions": (h, d, w), "rotation": {"widthDepth": True, "widthHeight": True, "depthHeight": True}}
        ]
        
        return orientations
    
    def find_possible_positions(self, space_matrix: np.ndarray, width: int, depth: int, height: int) -> List[Tuple[int, int, int]]:
        """Find all possible positions for an item of given dimensions in the space"""
        w_max, d_max, h_max = space_matrix.shape
        positions = []
        
        # Always place items against at least one surface for stability
        # This implementation prioritizes placing items at the bottom and back of the container
        for w in range(w_max - width + 1):
            for d in range(d_max - depth + 1):
                for h in range(h_max - height + 1):
                    # Check if the space is free
                    if not np.any(space_matrix[w:w+width, d:d+depth, h:h+height]):
                        # Prioritize positions that touch the back wall or other items
                        if (d == 0 or np.any(space_matrix[w:w+width, d-1, h:h+height])) and \
                           (h == 0 or np.any(space_matrix[w:w+width, d:d+depth, h-1])):
                            positions.append((w, d, h))
        
        # Sort positions by accessibility (prefer closer to open face and lower height)
        positions.sort(key=lambda pos: (pos[1], pos[2]))
        
        return positions
    
    def calculate_accessibility_score(self, space_matrix: np.ndarray, 
                                     start_w: int, start_d: int, start_h: int,
                                     end_w: int, end_d: int, end_h: int) -> float:
        """
        Calculate how accessible an item would be if placed at the given position
        Lower scores mean more accessible
        """
        # Factors that affect accessibility:
        # 1. Depth from open face (higher depth = harder to access)
        # 2. Height (higher = harder to access)
        # 3. Number of other items that need to be removed to access this item
        
        depth_factor = start_d * 2.0  # Depth is weighted higher
        height_factor = start_h * 1.0
        
        # Check if there are items in front of this position
        blocking_items = 0
        if start_d > 0:
            # Consider a path from open face to this item
            blocking_items = np.sum(space_matrix[start_w:end_w, 0:start_d, start_h:end_h])
        
        # Weighted score
        return depth_factor + height_factor + (blocking_items * 10.0)
    
    def update_space_matrix(self, space_matrix: np.ndarray, 
                          start_w: int, start_d: int, start_h: int,
                          end_w: int, end_d: int, end_h: int, 
                          value: int = 1) -> np.ndarray:
        """Update the space matrix, marking a region as occupied (1) or free (0)"""
        space_matrix[start_w:end_w, start_d:end_d, start_h:end_h] = value
        return space_matrix
    
    def optimize_placement_for_items(self, items: List[Item], containers: List[Container],
                                   existing_placements: Dict[str, List[ItemPlacement]]) -> Dict:
        """
        Find optimal placements for a list of items across available containers
        Returns placements and any necessary rearrangements
        """
        logger.info(f"Optimizing placement for {len(items)} items across {len(containers)} containers")
        
        # Sort items by priority (highest priority first)
        sorted_items = sorted(items, key=lambda x: (-x.priority, x.id))
        
        # Track placements and rearrangements
        placements = []
        rearrangements = []
        rearrangement_step = 1
        
        # First try to place items in their preferred zones
        for item in sorted_items:
            placed = False
            
            # First try preferred zone containers
            preferred_containers = [c for c in containers if c.zone == item.preferred_zone]
            for container in preferred_containers:
                # Get existing placements for this container
                container_placements = existing_placements.get(container.id, [])
                
                # Try to find placement
                placement = self.find_placement_for_item(item, container, container_placements)
                if placement:
                    # Add to placements
                    placements.append({
                        "itemId": item.id,
                        "containerId": container.id,
                        "position": placement
                    })
                    
                    # Update container space
                    self.reset_container_space(container.id)
                    placed = True
                    break
            
            # If not placed in preferred zone, try any container
            if not placed:
                other_containers = [c for c in containers if c.zone != item.preferred_zone]
                for container in other_containers:
                    # Get existing placements for this container
                    container_placements = existing_placements.get(container.id, [])
                    
                    # Try to find placement
                    placement = self.find_placement_for_item(item, container, container_placements)
                    if placement:
                        # Add to placements
                        placements.append({
                            "itemId": item.id,
                            "containerId": container.id,
                            "position": placement
                        })
                        
                        # Update container space
                        self.reset_container_space(container.id)
                        placed = True
                        break
            
            # If still not placed, try rearrangements
            if not placed:
                rearrangement_result = self.attempt_rearrangement(
                    item, containers, existing_placements, rearrangement_step, sorted_items
                )
                
                if rearrangement_result:
                    placements.append(rearrangement_result["placement"])
                    rearrangements.extend(rearrangement_result["steps"])
                    rearrangement_step += len(rearrangement_result["steps"])
                    placed = True
        
        return {
            "success": len(placements) == len(sorted_items),
            "placements": placements,
            "rearrangements": rearrangements
        }
    
    def attempt_rearrangement(self, item: Item, containers: List[Container],
                            existing_placements: Dict[str, List[ItemPlacement]],
                            start_step: int, items: Optional[List[Item]] = None) -> Optional[Dict]:
        """
        Attempt to rearrange items to make room for a new item
        Returns placement and rearrangement steps if successful
        """
        logger.info(f"Attempting rearrangement to place item {item.id}")
        
        # If no items provided, we can't do rearrangement
        if items is None:
            return None
        
        # This is a simplified rearrangement algorithm
        # In a real system, you would use more sophisticated approaches
        
        # Start with preferred zone containers
        preferred_containers = [c for c in containers if c.zone == item.preferred_zone]
        other_containers = [c for c in containers if c.zone != item.preferred_zone]
        all_containers = preferred_containers + other_containers
        
        for container in all_containers:
            # Get existing placements for this container
            container_placements = existing_placements.get(container.id, [])
            
            # Find low priority items that could be moved
            low_priority_placements = []
            for placement in container_placements:
                # Find the item associated with this placement
                placed_item = next((i for i in items if i.id == placement.item_id), None)
                if placed_item and placed_item.priority < item.priority:
                    low_priority_placements.append((placement, placed_item))
            
            # Sort by priority (lowest first)
            low_priority_placements.sort(key=lambda x: x[1].priority)
            
            # Try removing one low priority item at a time
            for removal_placement, removal_item in low_priority_placements:
                # Temporarily remove this placement
                temp_placements = [p for p in container_placements if p.id != removal_placement.id]
                
                # Check if the new item fits now
                placement = self.find_placement_for_item(item, container, temp_placements)
                if placement:
                    # Find a new container for the removed item
                    new_container = None
                    new_placement = None
                    
                    for other_container in containers:
                        if other_container.id != container.id:
                            other_container_placements = existing_placements.get(other_container.id, [])
                            other_placement = self.find_placement_for_item(
                                removal_item, other_container, other_container_placements
                            )
                            if other_placement:
                                new_container = other_container
                                new_placement = other_placement
                                break
                    
                    if new_container and new_placement:
                        # We found a valid rearrangement
                        steps = [
                            {
                                "step": start_step,
                                "action": "remove",
                                "itemId": removal_item.id,
                                "fromContainer": container.id,
                                "fromPosition": {
                                    "startCoordinates": {
                                        "width": removal_placement.start_width,
                                        "depth": removal_placement.start_depth,
                                        "height": removal_placement.start_height
                                    },
                                    "endCoordinates": {
                                        "width": removal_placement.end_width,
                                        "depth": removal_placement.end_depth,
                                        "height": removal_placement.end_height
                                    }
                                }
                            },
                            {
                                "step": start_step + 1,
                                "action": "place",
                                "itemId": removal_item.id,
                                "toContainer": new_container.id,
                                "toPosition": new_placement
                            },
                            {
                                "step": start_step + 2,
                                "action": "place",
                                "itemId": item.id,
                                "toContainer": container.id,
                                "toPosition": placement
                            }
                        ]
                        
                        return {
                            "placement": {
                                "itemId": item.id,
                                "containerId": container.id,
                                "position": placement
                            },
                            "steps": steps
                        }
        
        # Could not find a valid rearrangement
        return None
