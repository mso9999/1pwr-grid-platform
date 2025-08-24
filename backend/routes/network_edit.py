"""
Network element editing API routes
Handles CRUD operations for poles, connections, and conductors
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

router = APIRouter()

class PoleCreate(BaseModel):
    """Model for creating a new pole"""
    pole_id: Optional[str] = None
    latitude: float
    longitude: float
    pole_type: str = "POLE"
    pole_class: str = "LV"
    st_code_1: int = 0
    st_code_2: int = 0
    angle_class: str = "0-15"
    notes: Optional[str] = None

class PoleUpdate(BaseModel):
    """Model for updating an existing pole"""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    pole_type: Optional[str] = None
    pole_class: Optional[str] = None
    st_code_1: Optional[int] = None
    st_code_2: Optional[int] = None
    angle_class: Optional[str] = None
    notes: Optional[str] = None

class ConnectionCreate(BaseModel):
    """Model for creating a new customer connection"""
    connection_id: Optional[str] = None
    latitude: float
    longitude: float
    pole_id: str  # Associated pole
    customer_name: Optional[str] = None
    st_code_3: int = 0
    meter_number: Optional[str] = None
    notes: Optional[str] = None

class ConnectionUpdate(BaseModel):
    """Model for updating a connection"""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    pole_id: Optional[str] = None
    customer_name: Optional[str] = None
    st_code_3: Optional[int] = None
    meter_number: Optional[str] = None
    notes: Optional[str] = None

class ConductorCreate(BaseModel):
    """Model for creating a new conductor"""
    conductor_id: Optional[str] = None
    from_pole: str
    to_pole: str
    conductor_type: str = "LV"
    conductor_spec: str = "50"
    length: Optional[float] = None
    st_code_4: int = 0
    notes: Optional[str] = None

class ConductorUpdate(BaseModel):
    """Model for updating a conductor"""
    from_pole: Optional[str] = None
    to_pole: Optional[str] = None
    conductor_type: Optional[str] = None
    conductor_spec: Optional[str] = None
    length: Optional[float] = None
    st_code_4: Optional[int] = None
    notes: Optional[str] = None

class ConductorSplit(BaseModel):
    """Model for splitting a conductor at a point"""
    split_point: Dict[str, float]  # {lat, lng}
    new_pole_id: Optional[str] = None

# Import shared storage
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from storage import network_storage

@router.post("/poles/{site}")
async def create_pole(site: str, pole: PoleCreate):
    """Create a new pole in the network"""
    try:
        if site not in network_storage:
            network_storage[site] = {"poles": [], "conductors": [], "connections": [], "transformers": []}
        
        # Generate pole ID if not provided
        pole_id = pole.pole_id
        if not pole_id:
            # Extract site prefix and generate sequential ID
            existing_poles = network_storage[site].get("poles", [])
            pole_number = len(existing_poles) + 1
            pole_id = f"{site.upper()}_{pole_number:04d}"
        
        # Check for duplicate pole ID
        existing_poles = network_storage[site].get("poles", [])
        if any(p["pole_id"] == pole_id for p in existing_poles):
            raise HTTPException(status_code=400, detail=f"Pole ID {pole_id} already exists")
        
        # Create pole data
        new_pole = {
            "pole_id": pole_id,
            "latitude": pole.latitude,
            "longitude": pole.longitude,
            "pole_type": pole.pole_type,
            "pole_class": pole.pole_class,
            "st_code_1": pole.st_code_1,
            "st_code_2": pole.st_code_2,
            "angle_class": pole.angle_class,
            "notes": pole.notes,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Add to storage
        network_storage[site]["poles"].append(new_pole)
        
        from fastapi.responses import JSONResponse
        return JSONResponse(content={
            "success": True,
            "message": f"Pole {pole_id} created successfully",
            "pole": new_pole
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/poles/{site}/{pole_id}")
async def update_pole(site: str, pole_id: str, pole: PoleUpdate):
    """Update an existing pole"""
    try:
        if site not in network_storage:
            raise HTTPException(status_code=404, detail=f"Site {site} not found")
        
        poles = network_storage[site].get("poles", [])
        pole_index = next((i for i, p in enumerate(poles) if p["pole_id"] == pole_id), None)
        
        if pole_index is None:
            raise HTTPException(status_code=404, detail=f"Pole {pole_id} not found")
        
        # Update pole data
        update_data = pole.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        poles[pole_index].update(update_data)
        
        from fastapi.responses import JSONResponse
        return JSONResponse(content={
            "success": True,
            "message": f"Pole {pole_id} updated successfully",
            "pole": poles[pole_index]
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/poles/{site}/{pole_id}")
async def delete_pole(site: str, pole_id: str, force: bool = False):
    """Delete a pole and optionally its associated conductors"""
    try:
        if site not in network_storage:
            raise HTTPException(status_code=404, detail=f"Site {site} not found")
        
        poles = network_storage[site].get("poles", [])
        conductors = network_storage[site].get("conductors", [])
        
        # Find pole
        pole_index = next((i for i, p in enumerate(poles) if p["pole_id"] == pole_id), None)
        if pole_index is None:
            raise HTTPException(status_code=404, detail=f"Pole {pole_id} not found")
        
        # Check for connected conductors
        connected_conductors = [
            c for c in conductors 
            if c.get("from_pole") == pole_id or c.get("to_pole") == pole_id
        ]
        
        if connected_conductors and not force:
            raise HTTPException(
                status_code=400, 
                detail=f"Pole {pole_id} has {len(connected_conductors)} connected conductors. Use force=true to delete all."
            )
        
        # Delete pole
        deleted_pole = poles.pop(pole_index)
        
        # Delete connected conductors if force=true
        if force and connected_conductors:
            network_storage[site]["conductors"] = [
                c for c in conductors 
                if c.get("from_pole") != pole_id and c.get("to_pole") != pole_id
            ]
        
        from fastapi.responses import JSONResponse
        return JSONResponse(content={
            "success": True,
            "message": f"Pole {pole_id} deleted successfully",
            "deleted_pole": deleted_pole,
            "deleted_conductors": len(connected_conductors) if force else 0
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/connections/{site}/{connection_id}")
async def delete_connection(site: str, connection_id: str):
    """Delete a customer connection"""
    try:
        if site not in network_storage:
            raise HTTPException(status_code=404, detail=f"Site {site} not found")
        
        connections = network_storage[site].get("connections", [])
        
        # Find and remove connection
        connection_to_delete = next((c for c in connections if c["connection_id"] == connection_id), None)
        if connection_to_delete is None:
            raise HTTPException(status_code=404, detail=f"Connection {connection_id} not found")
        
        deleted_connection = connections.remove(connection_to_delete)
        
        return JSONResponse(content={
            "success": True,
            "message": f"Connection {connection_id} deleted successfully",
            "deleted_connection": deleted_connection
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/connections/{site}")
async def create_connection(site: str, connection: ConnectionCreate):
    """Create a new customer connection"""
    try:
        if site not in network_storage:
            network_storage[site] = {"poles": [], "conductors": [], "connections": [], "transformers": []}
        
        # Generate connection ID if not provided
        if not connection.connection_id:
            connection.connection_id = f"CONN_{uuid.uuid4().hex[:8].upper()}"
        
        # Verify pole exists
        poles = network_storage[site].get("poles", [])
        if not any(p["pole_id"] == connection.pole_id for p in poles):
            raise HTTPException(status_code=400, detail=f"Pole {connection.pole_id} not found")
        
        # Create connection data
        new_connection = {
            "connection_id": connection.connection_id,
            "latitude": connection.latitude,
            "longitude": connection.longitude,
            "pole_id": connection.pole_id,
            "customer_name": connection.customer_name,
            "st_code_3": connection.st_code_3,
            "meter_number": connection.meter_number,
            "notes": connection.notes,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Add to storage
        if "connections" not in network_storage[site]:
            network_storage[site]["connections"] = []
        network_storage[site]["connections"].append(new_connection)
        
        return {
            "success": True,
            "message": f"Connection {connection.connection_id} created successfully",
            "connection": new_connection
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conductors/{site}")
async def create_conductor(site: str, conductor: ConductorCreate):
    """Create a new conductor between two poles"""
    try:
        if site not in network_storage:
            raise HTTPException(status_code=404, detail=f"Site {site} not found")
        
        # Generate conductor ID if not provided
        if not conductor.conductor_id:
            conductor.conductor_id = f"COND_{uuid.uuid4().hex[:8].upper()}"
        
        # Verify both nodes exist (can be poles or connections)
        poles = network_storage[site].get("poles", [])
        connections = network_storage[site].get("connections", [])
        
        # Create a set of all valid node IDs
        pole_ids = {p["pole_id"] for p in poles}
        connection_ids = {c["pole_id"] for c in connections}
        all_node_ids = pole_ids | connection_ids
        
        if conductor.from_pole not in all_node_ids:
            raise HTTPException(status_code=400, detail=f"From pole {conductor.from_pole} not found")
        if conductor.to_pole not in all_node_ids:
            raise HTTPException(status_code=400, detail=f"To pole {conductor.to_pole} not found")
        
        # Calculate length if not provided
        if conductor.length is None:
            from_pole = next(p for p in poles if p["pole_id"] == conductor.from_pole)
            to_pole = next(p for p in poles if p["pole_id"] == conductor.to_pole)
            
            import math
            lat_diff = from_pole["latitude"] - to_pole["latitude"]
            lng_diff = from_pole["longitude"] - to_pole["longitude"]
            # Approximate distance in meters
            conductor.length = math.sqrt(lat_diff**2 + lng_diff**2) * 111000
        
        # Create conductor data
        new_conductor = {
            "conductor_id": conductor.conductor_id,
            "from_pole": conductor.from_pole,
            "to_pole": conductor.to_pole,
            "conductor_type": conductor.conductor_type,
            "conductor_spec": conductor.conductor_spec,
            "length": conductor.length,
            "st_code_4": conductor.st_code_4,
            "notes": conductor.notes,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Add to storage
        network_storage[site]["conductors"].append(new_conductor)
        
        return {
            "success": True,
            "message": f"Conductor {conductor.conductor_id} created successfully",
            "conductor": new_conductor
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/conductors/{site}/{conductor_id}")
async def update_conductor(site: str, conductor_id: str, conductor: ConductorUpdate):
    """Update an existing conductor"""
    try:
        if site not in network_storage:
            raise HTTPException(status_code=404, detail=f"Site {site} not found")
        
        conductors = network_storage[site].get("conductors", [])
        
        # Find the conductor
        conductor_index = None
        for i, c in enumerate(conductors):
            if c["conductor_id"] == conductor_id:
                conductor_index = i
                break
        
        if conductor_index is None:
            raise HTTPException(status_code=404, detail=f"Conductor {conductor_id} not found")
        
        # Update fields
        update_data = conductor.dict(exclude_unset=True)
        for key, value in update_data.items():
            conductors[conductor_index][key] = value
        conductors[conductor_index]["updated_at"] = datetime.utcnow().isoformat()
        
        from fastapi.responses import JSONResponse
        return JSONResponse(content={
            "success": True,
            "message": f"Conductor {conductor_id} updated successfully",
            "conductor": conductors[conductor_index]
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conductors/{site}/{conductor_id}/split")
async def split_conductor(site: str, conductor_id: str, split_data: ConductorSplit):
    """Split a conductor at a specific point by creating a new pole"""
    try:
        if site not in network_storage:
            raise HTTPException(status_code=404, detail=f"Site {site} not found")
        
        conductors = network_storage[site].get("conductors", [])
        poles = network_storage[site].get("poles", [])
        
        # Find conductor
        conductor_index = next((i for i, c in enumerate(conductors) if c["conductor_id"] == conductor_id), None)
        if conductor_index is None:
            raise HTTPException(status_code=404, detail=f"Conductor {conductor_id} not found")
        
        original_conductor = conductors[conductor_index]
        
        # Generate new pole ID if not provided
        if not split_data.new_pole_id:
            pole_number = len(poles) + 1
            split_data.new_pole_id = f"{site.upper()}_SPLIT_{pole_number:04d}"
        
        # Create new pole at split point
        new_pole = {
            "pole_id": split_data.new_pole_id,
            "latitude": split_data.split_point["lat"],
            "longitude": split_data.split_point["lng"],
            "pole_type": "POLE",
            "pole_class": original_conductor["conductor_type"],
            "st_code_1": 0,
            "st_code_2": 0,
            "angle_class": "I",  # Intermediate pole
            "notes": f"Created by splitting conductor {conductor_id}",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        poles.append(new_pole)
        
        # Create first segment (from original from_pole to new pole)
        segment1 = {
            "conductor_id": f"{conductor_id}_1",
            "from_pole": original_conductor["from_pole"],
            "to_pole": split_data.new_pole_id,
            "conductor_type": original_conductor["conductor_type"],
            "conductor_spec": original_conductor.get("conductor_spec", "50"),
            "length": original_conductor.get("length", 0) / 2,  # Approximate
            "st_code_4": original_conductor.get("st_code_4", 0),
            "notes": f"First segment of split conductor {conductor_id}",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Create second segment (from new pole to original to_pole)
        segment2 = {
            "conductor_id": f"{conductor_id}_2",
            "from_pole": split_data.new_pole_id,
            "to_pole": original_conductor["to_pole"],
            "conductor_type": original_conductor["conductor_type"],
            "conductor_spec": original_conductor.get("conductor_spec", "50"),
            "length": original_conductor.get("length", 0) / 2,  # Approximate
            "st_code_4": original_conductor.get("st_code_4", 0),
            "notes": f"Second segment of split conductor {conductor_id}",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Remove original conductor and add new segments
        conductors.pop(conductor_index)
        conductors.extend([segment1, segment2])
        
        return {
            "success": True,
            "message": f"Conductor {conductor_id} split successfully",
            "new_pole": new_pole,
            "segments": [segment1, segment2]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/conductors/{site}/{conductor_id}")
async def delete_conductor(site: str, conductor_id: str):
    """Delete a conductor"""
    try:
        if site not in network_storage:
            raise HTTPException(status_code=404, detail=f"Site {site} not found")
        
        conductors = network_storage[site].get("conductors", [])
        
        # Find and remove conductor
        conductor_index = next((i for i, c in enumerate(conductors) if c["conductor_id"] == conductor_id), None)
        if conductor_index is None:
            raise HTTPException(status_code=404, detail=f"Conductor {conductor_id} not found")
        
        deleted_conductor = conductors.pop(conductor_index)
        
        from fastapi.responses import JSONResponse
        return JSONResponse(content={
            "success": True,
            "message": f"Conductor {conductor_id} deleted successfully",
            "deleted_conductor": deleted_conductor
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
