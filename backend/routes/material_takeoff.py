"""
Material takeoff API routes
Generates bill of materials reports from network data
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Dict, Any
import io
import pandas as pd
from datetime import datetime

from utils.material_takeoff import MaterialTakeoffCalculator
from storage import network_storage

router = APIRouter()

@router.get("/material-takeoff/{site}")
async def get_material_takeoff(site: str):
    """
    Generate material takeoff report for a site
    Returns JSON with detailed bill of materials
    """
    try:
        if site not in network_storage:
            raise HTTPException(status_code=404, detail=f"Site {site} not found")
        
        network_data = network_storage[site]
        
        # Calculate material takeoff
        calculator = MaterialTakeoffCalculator(network_data)
        takeoff = calculator.calculate_takeoff()
        
        return JSONResponse(content={
            "success": True,
            "site": site,
            "generated_at": datetime.utcnow().isoformat(),
            "takeoff": takeoff
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/material-takeoff/{site}/excel")
async def export_material_takeoff_excel(site: str):
    """
    Export material takeoff report as Excel file
    """
    try:
        if site not in network_storage:
            raise HTTPException(status_code=404, detail=f"Site {site} not found")
        
        network_data = network_storage[site]
        
        # Calculate material takeoff
        calculator = MaterialTakeoffCalculator(network_data)
        takeoff = calculator.calculate_takeoff()
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Summary sheet
            summary_df = pd.DataFrame([takeoff['summary']])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Poles sheet
            if takeoff['poles']['details']:
                poles_df = pd.DataFrame(takeoff['poles']['details'])
                poles_df.to_excel(writer, sheet_name='Poles', index=False)
            
            # Conductors sheet
            if takeoff['conductors']['details']:
                conductors_df = pd.DataFrame(takeoff['conductors']['details'])
                conductors_df.to_excel(writer, sheet_name='Conductors', index=False)
            
            # Connections sheet
            connections_data = []
            for status, data in takeoff['connections']['by_status'].items():
                connections_data.append({
                    'Status Code': status,
                    'Description': data['description'],
                    'Quantity': data['count']
                })
            if connections_data:
                connections_df = pd.DataFrame(connections_data)
                connections_df.to_excel(writer, sheet_name='Connections', index=False)
            
            # Hardware sheet
            hardware_data = [{'Item': k.replace('_', ' ').title(), 'Quantity': v} 
                           for k, v in takeoff['hardware'].items()]
            hardware_df = pd.DataFrame(hardware_data)
            hardware_df.to_excel(writer, sheet_name='Hardware', index=False)
            
            # Totals sheet
            totals_df = pd.DataFrame([takeoff['totals']])
            totals_df.to_excel(writer, sheet_name='Totals', index=False)
            
            # Format worksheets
            workbook = writer.book
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#D3D3D3',
                'border': 1
            })
            
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                worksheet.set_column('A:Z', 15)  # Set column width
        
        # Prepare file for download
        output.seek(0)
        filename = f"{site}_material_takeoff_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return StreamingResponse(
            io.BytesIO(output.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/material-takeoff/{site}/summary")
async def get_material_takeoff_summary(site: str):
    """
    Get a quick summary of material takeoff
    """
    try:
        if site not in network_storage:
            raise HTTPException(status_code=404, detail=f"Site {site} not found")
        
        network_data = network_storage[site]
        
        # Calculate material takeoff
        calculator = MaterialTakeoffCalculator(network_data)
        takeoff = calculator.calculate_takeoff()
        
        # Create simplified summary
        summary = {
            "site": site,
            "poles": {
                "total": takeoff['summary']['total_poles'],
                "types": len(takeoff['poles']['by_type'])
            },
            "conductors": {
                "total": takeoff['summary']['total_conductors'],
                "length_km": round(takeoff['summary']['network_length_m'] / 1000, 3),
                "mv_km": round(takeoff['conductors']['by_type'].get('MV', {}).get('total_length_m', 0) / 1000, 3),
                "lv_km": round(takeoff['conductors']['by_type'].get('LV', {}).get('total_length_m', 0) / 1000, 3),
                "drop_km": round(takeoff['conductors']['by_type'].get('DROP', {}).get('total_length_m', 0) / 1000, 3)
            },
            "connections": {
                "total": takeoff['summary']['total_connections'],
                "meters_needed": takeoff['connections']['meters_needed'],
                "meter_boxes_needed": takeoff['connections']['meter_boxes_needed']
            },
            "hardware": takeoff['hardware']
        }
        
        return JSONResponse(content={
            "success": True,
            "summary": summary
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
