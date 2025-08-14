"""
1PWR Grid Platform - FastAPI Backend
Provides REST API for network data operations and calculations
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import json
import pickle
import tempfile
import shutil
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for module imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import existing modules
from modules.import_pipeline.excel_importer import ExcelImporter
from modules.data_cleaning.data_cleaner import DataCleaner
from modules.network_engine.voltage_calculator import VoltageCalculator
from modules.network_engine.network_validator import NetworkValidator
from modules.data_model.enhanced_model import EnhancedNetworkModel
from modules.data_model.data_converter import DataConverter
from modules.export_pipeline.excel_exporter import ExcelExporter

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
    print(f"\n=== Starting Excel upload for file: {file.filename} ===")
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Import using existing ExcelImporter
        print(f"Creating ExcelImporter with temp file: {tmp_path}")
        importer = ExcelImporter(tmp_path)
        print("Importing network data...")
        import_result = importer.import_all()
        
        # Check if import was successful
        if not import_result.get('success', False):
            errors = import_result.get('errors', ['Unknown import error'])
            raise ValueError(f"Import failed: {errors}")
        
        # Extract the actual data lists from the nested structure
        network_data = {
            'poles': import_result.get('poles', {}).get('poles', []),
            'conductors': import_result.get('conductors', {}).get('conductors', []),
            'connections': import_result.get('connections', {}).get('connections', []),
            'transformers': import_result.get('transformers', {}).get('transformers', [])
        }
        
        print(f"Extracted data: {len(network_data['poles'])} poles, {len(network_data['conductors'])} conductors")
        
        # Debug: Print sample pole IDs to understand format
        if network_data['poles']:
            sample_poles = network_data['poles'][:5]
            print(f"Sample pole IDs: {[p.get('pole_id', 'NO_ID') for p in sample_poles]}")
        
        # Debug: Print sample conductor references to understand format
        if network_data['conductors']:
            sample_conductors = network_data['conductors'][:5]
            print(f"Sample conductor refs: {[(c.get('from_pole'), c.get('to_pole')) for c in sample_conductors]}")
        
        # Merge connections as valid nodes for conductor reference matching
        # The Connections sheet contains customer connection points that are referenced by DropLines
        print(f"Processing {len(network_data['connections'])} customer connections...")
        
        # Add each connection as a node that can be referenced by conductors
        for connection in network_data['connections']:
            survey_id = connection.get('survey_id', '')
            if survey_id:
                # Add connection as a special node type for reference matching
                network_data['poles'].append({
                    'pole_id': survey_id,
                    'pole_name': survey_id,
                    'pole_type': 'CUSTOMER_CONNECTION',
                    'gps_lat': connection.get('gps_lat'),
                    'gps_lng': connection.get('gps_lng'),
                    'utm_x': connection.get('utm_x'),
                    'utm_y': connection.get('utm_y'),
                    'from_connections_sheet': True  # Mark source for debugging
                })
        
        print(f"After merging connections: {len(network_data['poles'])} total nodes (poles + customer connections)")
        
        # Clean the data
        cleaner = DataCleaner()
        cleaned_data, cleaning_report = cleaner.clean_data(network_data)
        
        # Extract site name from the actual data
        # Look at pole IDs to determine the site name (e.g., "KET_17_GA124" -> "KET")
        site_name = "UNKNOWN"
        if cleaned_data.get('poles') and len(cleaned_data['poles']) > 0:
            # Get the first pole ID and extract the site prefix
            first_pole_id = cleaned_data['poles'][0].get('pole_id', '')
            if first_pole_id and '_' in first_pole_id:
                # Extract the prefix before the first underscore
                site_name = first_pole_id.split('_')[0].upper()
            elif first_pole_id:
                # If no underscore, try to extract the alphabetic prefix
                import re
                match = re.match(r'^([A-Za-z]+)', first_pole_id)
                if match:
                    site_name = match.group(1).upper()
        
        # If we couldn't extract from pole IDs, fall back to filename
        if site_name == "UNKNOWN":
            site_name = file.filename.split('.')[0].upper()
            
        print(f"Extracted site name: {site_name}")
        
        # Store in memory
        network_storage[site_name] = cleaned_data
        
        # Debug: Log what's actually stored
        print(f"\n=== Data stored in network_storage[{site_name}] ===")
        print(f"Poles: {len(cleaned_data.get('poles', []))}")
        print(f"Conductors: {len(cleaned_data.get('conductors', []))}")
        print(f"Connections: {len(cleaned_data.get('connections', []))}")
        print(f"Transformers: {len(cleaned_data.get('transformers', []))}")
        if cleaned_data.get('conductors'):
            print(f"Sample conductor: {cleaned_data['conductors'][0]}")
        print(f"=== End storage debug ===\n")
        
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
        import traceback
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"\n=== ERROR in upload_excel ===")
        print(f"Error: {error_msg}")
        print(f"Traceback:\n{error_trace}")
        print(f"=== END ERROR ===")
        raise HTTPException(status_code=400, detail=error_msg)

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
            "pole_class": pole.get('angle_class', pole.get('pole_class', 'Unknown')),  # Check both field names
            "status": pole.get('status', 'as_designed'),
            "is_connection": pole.get('from_connections_sheet', False),
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
            "status": conductor.get('status', 'as_designed'),
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
async def validate_network(site: str = "default"):
    """Validate network topology and data integrity"""
    try:
        # Get network data from storage
        network_data = network_storage.get(site)
        if not network_data:
            raise HTTPException(status_code=404, detail=f"No network data found for site: {site}")
        
        # Create validator
        validator = NetworkValidator()
        
        # Validate network
        validation_results = validator.validate_network(
            poles=network_data.get('poles', []),
            conductors=network_data.get('conductors', [])
        )
        
        return {
            "success": True,
            "site": site,
            "results": validation_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export/network-report")
async def export_network_report(
    site: str = "default",
    include_voltage: bool = True,
    include_validation: bool = True
):
    """Generate comprehensive network report in Excel format"""
    try:
        # Get network data from storage
        network_data = network_storage.get(site)
        if not network_data:
            raise HTTPException(status_code=404, detail=f"No network data found for site: {site}")
        
        # Get voltage results if requested
        voltage_results = None
        if include_voltage:
            voltage_results = voltage_storage.get(site)
        
        # Get validation results if requested
        validation_results = None
        if include_validation:
            validator = NetworkValidator()
            validation_results = validator.validate_network(
                poles=network_data.get('poles', []),
                conductors=network_data.get('conductors', [])
            )
        
        # Create exporter and generate report
        exporter = ExcelExporter()
        output_path = exporter.export_network_report(
            network_data=network_data,
            voltage_results=voltage_results,
            validation_results=validation_results,
            site_name=site
        )
        
        # Return file for download
        return FileResponse(
            path=output_path,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            filename=os.path.basename(output_path)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export/field-report")
async def export_field_report(request: dict):
    """Generate field team report in Excel format"""
    try:
        site_name = request.get("site", "Unknown")
        work_completed = request.get("work_completed", [])
        pending_work = request.get("pending_work", [])
        issues = request.get("issues", [])
        
        # Create exporter and generate report
        exporter = ExcelExporter()
        output_path = exporter.export_field_report(
            site_name=site_name,
            work_completed=work_completed,
            pending_work=pending_work,
            issues=issues
        )
        
        # Return file for download
        return FileResponse(
            path=output_path,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            filename=os.path.basename(output_path)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
