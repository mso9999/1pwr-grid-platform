"""
1PWR Grid Platform - FastAPI Backend
Provides REST API for network data operations and calculations
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import os
import traceback
import shutil
import sys
import tempfile
from pathlib import Path
from datetime import datetime
import math
import numpy as np

# Add current directory to path for module imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import existing modules
try:
    from utils.excel_importer import ExcelImporter
    from utils.voltage_calculator import VoltageCalculator
    from validators.network_validator import NetworkValidator
    from storage import network_storage  # Import shared storage
except ImportError as e:
    print(f"Import error: {e}")
    # Create stub classes if modules don't exist
    class ExcelImporter:
        def __init__(self, file_path):
            self.file_path = file_path
            
        def import_excel(self, *args, **kwargs):
            return {}
    
    class VoltageCalculator:
        def calculate_voltage_drop(self, *args, **kwargs):
            return {}
    
    class ReportExporter:
        def export_network_report(self, *args, **kwargs):
            return "report.xlsx"

from validators.network_validator import NetworkValidator

try:
    from modules.data_model.enhanced_model import EnhancedNetworkModel
    from modules.data_model.data_converter import DataConverter
    from modules.export_pipeline.excel_exporter import ExcelExporter
except ImportError:
    # Create stub classes if modules don't exist
    class EnhancedNetworkModel:
        pass
    
    class DataConverter:
        pass
    
    class ExcelExporter:
        pass

app = FastAPI(title="1PWR Grid Platform API", version="0.1.0")

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for voltage data (network storage imported from storage.py)
voltage_storage: Dict[str, Any] = {}

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
        network_data = importer.import_excel()
        
        # Check if import was successful
        if not network_data:
            raise ValueError(f"Import failed: No data returned")
        
        # The import_excel method returns the data directly
        # network_data already has the correct structure with poles, conductors, etc.
        
        print(f"Extracted data: {len(network_data.get('poles', []))} poles, {len(network_data.get('conductors', []))} conductors")
        
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
        
        # Update connections with proper st_code values
        for connection in network_data['connections']:
            # Keep st_code_3 as imported, don't overwrite with non-existent status_code
            connection['st_code_3'] = connection.get('st_code_3', 0)
            connection['st_code_1'] = connection.get('st_code_1', 0)
            connection['st_code_2'] = connection.get('st_code_2', 'NA')
        
        # Create a set of valid node IDs for conductor validation
        valid_node_ids = set()
        for pole in network_data['poles']:
            valid_node_ids.add(pole.get('pole_id'))
        for connection in network_data['connections']:
            survey_id = connection.get('survey_id')
            if survey_id:
                valid_node_ids.add(survey_id)
        
        print(f"Total nodes: {len(network_data['poles'])} poles, {len(network_data['connections'])} connections")
        
        # Skip data cleaning for now (DataCleaner not implemented)
        cleaned_data = network_data
        cleaning_report = {"cleaned": True}
        
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

def sanitize_value(value):
    """
    Recursively sanitize values for JSON serialization
    Replaces NaN/Infinity with None (null in JSON)
    """
    if value is None:
        return None
    
    # Handle numpy types
    if hasattr(value, 'item'):  # numpy scalar
        value = value.item()
    
    # Handle dictionaries recursively
    if isinstance(value, dict):
        return {k: sanitize_value(v) for k, v in value.items()}
    
    # Handle lists recursively
    if isinstance(value, (list, tuple)):
        return [sanitize_value(item) for item in value]
    
    if isinstance(value, (int, str, bool)):
        return value
    
    if isinstance(value, (float, np.floating)):
        if math.isnan(value) or math.isinf(value):
            return None
        return float(value)  # Convert numpy float to Python float
    
    if isinstance(value, (np.integer)):
        return int(value)  # Convert numpy int to Python int
    
    return value

@app.get("/api/network/{site}")
def get_network(site: str):
    """
    Get network data for a specific site
    Returns poles, connections, conductors, etc.
    """
    print(f"\n=== GET /api/network/{site} ===")
    print(f"Available sites in storage: {list(network_storage.keys())}")
    
    if site not in network_storage:
        return JSONResponse(
            status_code=404,
            content={"error": f"No network data for site {site}"}
        )
    
    network_data = network_storage[site]
    print(f"Retrieved data for {site}: {len(network_data.get('poles', []))} poles, {len(network_data.get('connections', []))} connections")
    
    # Format for frontend consumption
    formatted_data = {
        "poles": [],
        "connections": [],
        "conductors": [],
        "transformers": [],
        "generation": []
    }
    
    # Process poles
    poles_list = network_data.get('poles', [])
    print(f"Processing {len(poles_list)} poles...")
    for pole in poles_list:
        formatted_data['poles'].append({
                "id": pole.get('pole_id'),
                "lat": sanitize_value(pole.get('latitude', pole.get('gps_lat'))),
                "lng": sanitize_value(pole.get('longitude', pole.get('gps_lng'))),
                "type": pole.get('pole_type', 'standard'),
                "pole_class": pole.get('angle_class', pole.get('pole_class', 'Unknown')),  # Check both field names
                "status": pole.get('status', 'as_designed'),
                "st_code_1": pole.get('st_code_1', 0),  # Pass through status code 1
                "st_code_2": pole.get('st_code_2', 'NA'),  # Pass through status code 2
                "st_code_3": pole.get('st_code_3', 0),  # Pass through status code 3
                "utm_x": sanitize_value(pole.get('utm_x')),
                "utm_y": sanitize_value(pole.get('utm_y'))
            })
    
    # Process connections separately
    connections_list = network_data.get('connections', [])
    print(f"Processing {len(connections_list)} connections...")
    for connection in connections_list:
        formatted_data['connections'].append({
            "id": connection.get('survey_id'),
            "lat": sanitize_value(connection.get('latitude', connection.get('gps_lat'))),
            "lng": sanitize_value(connection.get('longitude', connection.get('gps_lng'))),
            "type": 'customer_connection',
            "status": connection.get('status', 'planned'),
            "st_code_1": connection.get('st_code_1', 0),
            "st_code_2": connection.get('st_code_2', 'NA'),
            "st_code_3": connection.get('st_code_3', 0),  # Now properly populated from status_code
            "meter_serial": connection.get('meter_serial'),
            "subnetwork": connection.get('subnetwork', 'main'),
            "utm_x": sanitize_value(connection.get('utm_x')),
            "utm_y": sanitize_value(connection.get('utm_y'))
        })
    
    # Process conductors
    conductors_list = network_data.get('conductors', [])
    print(f"Processing {len(conductors_list)} conductors...")
    for conductor in conductors_list:
        formatted_data['conductors'].append({
            "id": conductor.get('conductor_id'),
            "from": conductor.get('from_pole'),
            "to": conductor.get('to_pole'),
            "type": conductor.get('conductor_type', 'distribution'),
            "status": conductor.get('status', 'as_designed'),
            "length": sanitize_value(conductor.get('length_m'))
        })
    
    # Process transformers
    transformers_list = network_data.get('transformers', [])
    print(f"Processing {len(transformers_list)} transformers...")
    for transformer in transformers_list:
        formatted_data['transformers'].append({
            "id": transformer.get('transformer_id'),
            "lat": sanitize_value(transformer.get('gps_lat')),
            "lng": sanitize_value(transformer.get('gps_lng')),
            "rating": sanitize_value(transformer.get('rating_kva')),
            "pole_id": transformer.get('pole_id')
        })
    
    # Add generation site - find the source pole from voltage calculations
    # The source pole is the generation/substation location
    
    # Check for manual override from API or hardcoded value
    manual_generation_pole_id = None  # Change this to hardcode, e.g., "KET_02_BB1"
    
    # Check for dynamic override set via API
    if 'generation_overrides' in globals() and site in generation_overrides:
        manual_generation_pole_id = generation_overrides[site]
        print(f"Using API-set generation override for {site}: {manual_generation_pole_id}")
    
    try:
        from utils.voltage_calculator import VoltageCalculator
        
        if manual_generation_pole_id:
            # Use manual override
            source_pole_id = manual_generation_pole_id
            print(f"Using manual generation site override: {source_pole_id}")
        else:
            # Auto-detect using MV connectivity analysis
            calculator = VoltageCalculator()
            calculator._build_network(poles=network_data.get('poles', []), conductors=network_data.get('conductors', []))
            source_pole_id = calculator._find_source_pole(poles=network_data.get('poles', []), conductors=network_data.get('conductors', []))
        
        if source_pole_id:
            # Find the source pole data - check different field name variations
            source_pole = next((p for p in poles_list if p.get('pole_id') == source_pole_id or p.get('id') == source_pole_id), None)
            if source_pole:
                print(f"Found source pole: {source_pole_id}")
                # Get lat/lng from different possible field names
                lat = source_pole.get('latitude', source_pole.get('gps_lat', source_pole.get('lat')))
                lng = source_pole.get('longitude', source_pole.get('gps_lng', source_pole.get('lng')))
                formatted_data['generation'].append({
                    'id': f'GEN_{source_pole_id}',
                    'pole_id': source_pole_id,
                    'lat': lat,
                    'lng': lng,
                    'type': 'substation',
                    'name': f'Generation Site at {source_pole_id}',
                    'capacity': 'Unknown'
                })
                print(f"Added generation site at pole {source_pole_id}")
    except Exception as e:
        print(f"Could not determine generation site: {e}")
    
    print(f"Generation sites: {formatted_data.get('generation', [])}")
    print(f"Generation in formatted_data: {formatted_data.get('generation', 'NOT FOUND')}")
    
    # Create response without sanitization first to debug
    response_data = {
        "site": site,
        "data": formatted_data,
        "stats": {
            "total_poles": len(formatted_data['poles']),
            "total_conductors": len(formatted_data['conductors']),
            "total_transformers": len(formatted_data['transformers']),
            "total_generation": len(formatted_data.get('generation', []))
        }
    }
    
    print(f"Returning formatted data: {len(formatted_data['poles'])} poles, {len(formatted_data['connections'])} connections, {len(formatted_data['conductors'])} conductors, {len(formatted_data['transformers'])} transformers")
    
    # Sanitize the entire response to handle NaN/Infinity values
    sanitized_response = sanitize_value(response_data)
    print(f"Returning sanitized response...")
    return JSONResponse(content=sanitized_response)

@app.post("/api/network/{site}/generation")
async def update_generation_site(site: str, request: Request):
    """
    Update the generation site location for a specific network
    """
    if site not in network_storage:
        raise HTTPException(status_code=404, detail=f"Site {site} not found")
    
    body = await request.json()
    pole_id = body.get('pole_id')
    if not pole_id:
        raise HTTPException(status_code=400, detail="pole_id is required")
    
    # Store the manual generation site override
    if 'generation_overrides' not in globals():
        global generation_overrides
        generation_overrides = {}
    
    generation_overrides[site] = pole_id
    
    return JSONResponse(content={
        "success": True,
        "message": f"Generation site for {site} updated to {pole_id}",
        "pole_id": pole_id
    })

@app.get("/api/export/{site}")
async def export_network_report(site: str):
    """
    Export network report to Excel
    """
    try:
        print(f"\n=== Starting Excel export for site: {site} ===")
        
        if site not in network_storage:
            raise HTTPException(status_code=404, detail=f"No network data for site {site}")
        
        network_data = network_storage[site]
        print(f"Network data found: {len(network_data.get('poles', []))} poles, {len(network_data.get('conductors', []))} conductors")
        
        validation_results = None
        voltage_results = None
        
        # Get validation results if available
        try:
            validator = NetworkValidator()
            validation_results = validator.validate_network(network_data)
            print(f"Validation results generated")
        except Exception as e:
            print(f"Validation skipped: {e}")
            pass
        
        # Get voltage results if available
        if site in voltage_storage:
            voltage_results = voltage_storage[site]
            print(f"Voltage results found")
        
        # Create report
        print(f"Creating ReportExporter...")
        exporter = ReportExporter()
        output_file = exporter.export_network_report(
            network_data=network_data,
            validation_results=validation_results,
            voltage_results=voltage_results,
            site_name=site
        )
        
        print(f"Report generated: {output_file}")
        
        # Check if file exists
        if not os.path.exists(output_file):
            raise HTTPException(status_code=500, detail=f"Report file not found: {output_file}")
        
        # Return file for download
        return FileResponse(
            path=output_file,
            filename=f"{site}_network_report.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"=== ERROR in export_network_report ===")
        print(f"Error: {e}")
        import traceback
        print(f"Traceback:\n{traceback.format_exc()}")
        print(f"=== END ERROR ===")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/voltage/{site}")
async def calculate_voltage_endpoint(site: str, request: VoltageRequest):
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
        
        # Perform calculations using the correct method
        results = calculator.calculate_voltage_drop(
            poles=network_data.get('poles', []),
            conductors=network_data.get('conductors', []),
            source_voltage=request.source_voltage,
            source_pole_id=getattr(request, 'source_pole_id', None),
            power_factor=getattr(request, 'power_factor', 0.85)
        )
        
        # Identify violations from pole voltages
        violations = []
        for pole_id, pole_data in results.get('pole_voltages', {}).items():
            voltage_drop_percent = pole_data.get('voltage_drop_percent', 0)
            if voltage_drop_percent > request.voltage_threshold:
                violations.append({
                    "node": pole_id,
                    "voltage": pole_data.get('voltage', 0),
                    "drop_percent": voltage_drop_percent
                })
        
        # Store results for later use
        voltage_storage[request.site] = results
        
        return CalculationResponse(
            success=True,
            message="Voltage calculation complete",
            results={
                "voltages": {pole_id: data['voltage'] for pole_id, data in results.get('pole_voltages', {}).items()},
                "violations": violations,
                "max_drop": results.get('statistics', {}).get('max_voltage_drop_percent', 0),
                "statistics": results.get('statistics', {})
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

@app.get("/api/validate/{site}")
async def validate_network(site: str = "default"):
    """Validate network topology and data integrity"""
    try:
        # Get network data from storage
        network_data = network_storage.get(site)
        if not network_data:
            raise HTTPException(status_code=404, detail=f"No network data found for site: {site}")
        
        # Create validator
        validator = NetworkValidator()
        
        # Get poles and conductors
        poles = network_data.get('poles', [])
        conductors = network_data.get('conductors', [])
        
        # Validate network topology
        validation_results = validator.validate_network(
            poles=poles,
            conductors=conductors
        )
        
        # Add conductor length validation
        length_issues = validator.validate_conductor_lengths(conductors)
        if length_issues:
            validation_results['conductor_length_issues'] = length_issues
        
        # Add pole coordinate validation
        coordinate_issues = validator.validate_pole_coordinates(poles)
        if coordinate_issues:
            validation_results['coordinate_issues'] = coordinate_issues
        
        # Add pole spacing validation
        spacing_issues = validator.validate_pole_spacing(poles, conductors)
        if spacing_issues:
            validation_results['spacing_issues'] = spacing_issues
        
        # Add status code validation
        pole_status_issues = validator.validate_status_codes(poles, 'pole')
        conductor_status_issues = validator.validate_status_codes(conductors, 'conductor')
        if pole_status_issues or conductor_status_issues:
            validation_results['status_code_issues'] = {
                'poles': pole_status_issues,
                'conductors': conductor_status_issues
            }
        
        # Calculate overall validation statistics
        total_issues = (
            len(validation_results.get('orphaned_poles', [])) +
            len(validation_results.get('invalid_conductors', [])) +
            len(validation_results.get('duplicate_pole_ids', [])) +
            len(length_issues) +
            len(coordinate_issues) +
            len(spacing_issues) +
            len(pole_status_issues) +
            len(conductor_status_issues)
        )
        
        validation_results['statistics']['total_issues'] = total_issues
        validation_results['statistics']['issue_types'] = {
            'topology': len(validation_results.get('orphaned_poles', [])) + len(validation_results.get('invalid_conductors', [])),
            'data_quality': len(validation_results.get('duplicate_pole_ids', [])) + len(coordinate_issues),
            'physical': len(length_issues) + len(spacing_issues),
            'status': len(pole_status_issues) + len(conductor_status_issues)
        }
        
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
                network_data.get('poles', []),
                network_data.get('conductors', []),
                network_data.get('connections', [])
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

# Register network editing routes
from routes.network_edit import router as network_edit_router
app.include_router(network_edit_router, prefix="/api/network", tags=["network-edit"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
