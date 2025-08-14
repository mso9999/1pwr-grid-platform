"""
1PWR Grid Platform - FastAPI Backend
Provides REST API for network data operations and calculations
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import sys
import os
import json
import io
import tempfile
from pathlib import Path

# Add parent directory to path for module imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import existing modules
from modules.import_pipeline.excel_importer import ExcelImporter
from modules.import_pipeline.pickle_importer import PickleImporter
from modules.network_engine.voltage_calculator import VoltageCalculator
from modules.network_engine.network_validator import NetworkValidator
from modules.data_cleaning.data_cleaner import DataCleaner
from modules.data_model.enhanced_model import EnhancedNetworkModel
from modules.data_model.data_converter import DataConverter

app = FastAPI(title="1PWR Grid Platform API", version="0.1.0")

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for now (will move to PostgreSQL)
network_storage: Dict[str, Any] = {}

class NetworkRequest(BaseModel):
    """Request model for network operations"""
    site: str
    data: Dict[str, Any]

class VoltageRequest(BaseModel):
    """Request model for voltage calculations"""
    site: str
    source_voltage: float = 11000.0
    voltage_threshold: float = 7.0

class CalculationResponse(BaseModel):
    """Response model for calculations"""
    success: bool
    message: str
    results: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None

@app.get("/")
async def root():
    """API health check"""
    return {"status": "healthy", "service": "1PWR Grid Platform API"}

@app.post("/api/upload/excel")
async def upload_excel(file: UploadFile = File(...)):
    """
    Upload and process Excel file from uGridPLAN
    Returns processed network data
    """
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Import using existing ExcelImporter
        importer = ExcelImporter(tmp_path)
        network_data = importer.import_network()
        
        # Clean the data
        cleaner = DataCleaner()
        cleaned_data = cleaner.clean_network_data(network_data)
        
        # Extract site name from filename
        site_name = file.filename.split('.')[0].upper()
        
        # Store in memory
        network_storage[site_name] = cleaned_data
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        return JSONResponse(content={
            "success": True,
            "message": f"Successfully imported {file.filename}",
            "site": site_name,
            "stats": {
                "poles": len(cleaned_data.get('poles', [])),
                "conductors": len(cleaned_data.get('conductors', [])),
                "transformers": len(cleaned_data.get('transformers', []))
            }
        })
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/upload/pickle")
async def upload_pickle(file: UploadFile = File(...)):
    """
    Upload and process Pickle file from legacy uGridPLAN
    """
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Import using existing PickleImporter
        importer = PickleImporter(tmp_path)
        network_data = importer.import_network()
        
        # Extract site name
        site_name = file.filename.split('.')[0].upper()
        
        # Store in memory
        network_storage[site_name] = network_data
        
        # Clean up
        os.unlink(tmp_path)
        
        return JSONResponse(content={
            "success": True,
            "message": f"Successfully imported {file.filename}",
            "site": site_name
        })
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/network/{site}")
async def get_network(site: str):
    """
    Get network data for a specific site
    Returns data formatted for map visualization
    """
    if site not in network_storage:
        # Return sample data if no real data loaded
        return JSONResponse(content={
            "site": site,
            "data": {
                "poles": [],
                "connections": [],
                "conductors": [],
                "transformers": []
            },
            "message": "No data loaded. Please upload Excel or Pickle file."
        })
    
    network_data = network_storage[site]
    
    # Format for frontend consumption
    formatted_data = {
        "poles": [],
        "connections": [],
        "conductors": [],
        "transformers": []
    }
    
    # Process poles
    for pole in network_data.get('poles', []):
        formatted_data['poles'].append({
            "id": pole.get('pole_id'),
            "lat": pole.get('gps_lat'),
            "lng": pole.get('gps_lng'),
            "type": pole.get('pole_type', 'standard'),
            "status": pole.get('status', 'as_designed'),
            "utm_x": pole.get('utm_x'),
            "utm_y": pole.get('utm_y')
        })
    
    # Process conductors
    for conductor in network_data.get('conductors', []):
        formatted_data['conductors'].append({
            "id": conductor.get('conductor_id'),
            "from": conductor.get('from_pole'),
            "to": conductor.get('to_pole'),
            "type": conductor.get('conductor_type', 'distribution'),
            "length": conductor.get('length_m')
        })
    
    # Process transformers
    for transformer in network_data.get('transformers', []):
        formatted_data['transformers'].append({
            "id": transformer.get('transformer_id'),
            "lat": transformer.get('gps_lat'),
            "lng": transformer.get('gps_lng'),
            "rating": transformer.get('rating_kva'),
            "pole_id": transformer.get('pole_id')
        })
    
    return JSONResponse(content={
        "site": site,
        "data": formatted_data,
        "stats": {
            "total_poles": len(formatted_data['poles']),
            "total_conductors": len(formatted_data['conductors']),
            "total_transformers": len(formatted_data['transformers'])
        }
    })

@app.post("/api/calculate/voltage")
async def calculate_voltage(request: VoltageRequest):
    """
    Calculate voltage drop for network
    Returns voltage at each node and identifies violations
    """
    try:
        if request.site not in network_storage:
            raise HTTPException(status_code=404, detail=f"No network data for site {request.site}")
        
        network_data = network_storage[request.site]
        
        # Initialize calculator
        calculator = VoltageCalculator()
        
        # Perform calculations
        results = calculator.calculate_network_voltage(
            network_data,
            source_voltage=request.source_voltage,
            voltage_threshold=request.voltage_threshold
        )
        
        # Identify violations
        violations = []
        for node_id, voltage in results.get('node_voltages', {}).items():
            voltage_drop_percent = ((request.source_voltage - voltage) / request.source_voltage) * 100
            if voltage_drop_percent > request.voltage_threshold:
                violations.append({
                    "node": node_id,
                    "voltage": voltage,
                    "drop_percent": voltage_drop_percent
                })
        
        return CalculationResponse(
            success=True,
            message="Voltage calculation complete",
            results={
                "voltages": results.get('node_voltages', {}),
                "violations": violations,
                "max_drop": max(
                    ((request.source_voltage - v) / request.source_voltage) * 100
                    for v in results.get('node_voltages', {}).values()
                ) if results.get('node_voltages') else 0
            }
        )
        
    except Exception as e:
        return CalculationResponse(
            success=False,
            message=str(e),
            errors=[str(e)]
        )

@app.post("/api/validate/network")
async def validate_network(request: NetworkRequest):
    """
    Validate network topology and constraints
    Returns validation results and identified issues
    """
    try:
        # Initialize validator
        validator = NetworkValidator()
        
        # Run validation
        is_valid, issues = validator.validate_network(request.data)
        
        return CalculationResponse(
            success=is_valid,
            message="Validation complete" if is_valid else "Validation found issues",
            results={"issues": issues}
        )
        
    except Exception as e:
        return CalculationResponse(
            success=False,
            message=str(e),
            errors=[str(e)]
        )

@app.get("/api/sites")
async def list_sites():
    """
    List all sites with loaded data
    """
    sites = []
    for site_name, data in network_storage.items():
        sites.append({
            "name": site_name,
            "poles": len(data.get('poles', [])),
            "conductors": len(data.get('conductors', [])),
            "transformers": len(data.get('transformers', []))
        })
    
    return JSONResponse(content={"sites": sites})

@app.post("/api/export/excel/{site}")
async def export_excel(site: str):
    """
    Export network data to Excel format
    Returns Excel file for download
    """
    if site not in network_storage:
        raise HTTPException(status_code=404, detail=f"No data for site {site}")
    
    # TODO: Implement Excel export using openpyxl
    # For now, return JSON
    return JSONResponse(content={
        "message": "Excel export not yet implemented",
        "site": site
    })

@app.delete("/api/network/{site}")
async def delete_network(site: str):
    """
    Remove network data for a site
    """
    if site in network_storage:
        del network_storage[site]
        return JSONResponse(content={"success": True, "message": f"Deleted data for {site}"})
    else:
        raise HTTPException(status_code=404, detail=f"No data for site {site}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
