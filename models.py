import datetime
from app import db
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

class Item(db.Model):
    """Model representing a cargo item"""
    __tablename__ = 'items'
    
    id = Column(String(50), primary_key=True)  # Item ID
    name = Column(String(100), nullable=False)
    width = Column(Float, nullable=False)  # in cm
    depth = Column(Float, nullable=False)  # in cm
    height = Column(Float, nullable=False)  # in cm
    mass = Column(Float, nullable=False)  # in kg
    priority = Column(Integer, nullable=False)  # 0-100
    expiry_date = Column(DateTime, nullable=True)  # ISO format date
    usage_limit = Column(Integer, nullable=False)  # Number of uses
    remaining_uses = Column(Integer, nullable=False)  # Current uses left
    preferred_zone = Column(String(100), nullable=True)
    is_waste = Column(Boolean, default=False)  # Flag for waste items
    
    placements = relationship("ItemPlacement", back_populates="item", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Item {self.id}: {self.name}>"
    
    def to_dict(self):
        """Convert item to dictionary for API response"""
        return {
            "itemId": self.id,
            "name": self.name,
            "width": self.width,
            "depth": self.depth,
            "height": self.height,
            "mass": self.mass,
            "priority": self.priority,
            "expiryDate": self.expiry_date.isoformat() if self.expiry_date else None,
            "usageLimit": self.usage_limit,
            "remainingUses": self.remaining_uses,
            "preferredZone": self.preferred_zone,
            "isWaste": self.is_waste
        }
    
    def is_expired(self):
        """Check if the item is expired"""
        if not self.expiry_date:
            return False
        return datetime.datetime.now() > self.expiry_date
    
    def is_used_up(self):
        """Check if the item has reached its usage limit"""
        return self.remaining_uses <= 0
    
    def should_be_waste(self):
        """Check if the item should be marked as waste"""
        return self.is_expired() or self.is_used_up()


class Container(db.Model):
    """Model representing a storage container"""
    __tablename__ = 'containers'
    
    id = Column(String(50), primary_key=True)  # Container ID
    zone = Column(String(100), nullable=False)
    width = Column(Float, nullable=False)  # in cm
    depth = Column(Float, nullable=False)  # in cm
    height = Column(Float, nullable=False)  # in cm
    
    placements = relationship("ItemPlacement", back_populates="container", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Container {self.id} in {self.zone}>"
    
    def to_dict(self):
        """Convert container to dictionary for API response"""
        return {
            "containerId": self.id,
            "zone": self.zone,
            "width": self.width,
            "depth": self.depth,
            "height": self.height
        }


class ItemPlacement(db.Model):
    """Model representing the placement of an item in a container"""
    __tablename__ = 'item_placements'
    
    id = Column(Integer, primary_key=True)
    item_id = Column(String(50), ForeignKey('items.id'), nullable=False)
    container_id = Column(String(50), ForeignKey('containers.id'), nullable=False)
    
    # Start coordinates (origin at the bottom left of the open face)
    start_width = Column(Float, nullable=False)
    start_depth = Column(Float, nullable=False)
    start_height = Column(Float, nullable=False)
    
    # End coordinates
    end_width = Column(Float, nullable=False)
    end_depth = Column(Float, nullable=False)
    end_height = Column(Float, nullable=False)
    
    # Rotation flags
    rotated_width_depth = Column(Boolean, default=False)  # Swapped width and depth
    rotated_width_height = Column(Boolean, default=False)  # Swapped width and height
    rotated_depth_height = Column(Boolean, default=False)  # Swapped depth and height
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    item = relationship("Item", back_populates="placements")
    container = relationship("Container", back_populates="placements")
    
    def __repr__(self):
        return f"<ItemPlacement: {self.item_id} in {self.container_id}>"
    
    def to_dict(self):
        """Convert placement to dictionary for API response"""
        return {
            "itemId": self.item_id,
            "containerId": self.container_id,
            "position": {
                "startCoordinates": {
                    "width": self.start_width,
                    "depth": self.start_depth,
                    "height": self.start_height
                },
                "endCoordinates": {
                    "width": self.end_width,
                    "depth": self.end_depth,
                    "height": self.end_height
                }
            },
            "rotated": {
                "widthDepth": self.rotated_width_depth,
                "widthHeight": self.rotated_width_height,
                "depthHeight": self.rotated_depth_height
            }
        }


class Log(db.Model):
    """Model for tracking all actions in the system"""
    __tablename__ = 'logs'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    action_type = Column(String(50), nullable=False)  # placement, retrieval, waste, rearrangement
    item_id = Column(String(50), ForeignKey('items.id'), nullable=True)
    container_id = Column(String(50), ForeignKey('containers.id'), nullable=True)
    astronaut_id = Column(String(50), nullable=True)  # In case we track who performed the action
    details = Column(String(500), nullable=True)  # Additional details about the action
    
    def __repr__(self):
        return f"<Log {self.id}: {self.action_type}>"
    
    def to_dict(self):
        """Convert log to dictionary for API response"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "actionType": self.action_type,
            "itemId": self.item_id,
            "containerId": self.container_id,
            "astronautId": self.astronaut_id,
            "details": self.details
        }
