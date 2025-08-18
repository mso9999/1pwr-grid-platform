"""
As-built tracking API routes
Handles field construction tracking and comparison with planned network
"""

from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Dict, Any, List
from datetime import datetime
import io
import pandas as pd
import json

from models.as_built import (
    AsBuiltPole, AsBuiltConnection, AsBuiltConductor,
    AsBuiltSnapshot, AsBuiltComparison
)
from utils.as_built_tracker import AsBuiltTracker
from storage import network_storage, as_built_storage

router = APIRouter()

@router.post("/as-built/{site}/snapshot")
async def create_as_built_snapshot(
    site: str,
    snapshot_data: Dict[str, Any] = Body(...)
):
    """
    Create a new as-built snapshot from field data
    """
    try:
        if site not in network_storage:
            raise HTTPException(status_code=404, detail=f"Site {site} not found")
        
        # Create snapshot
        snapshot = AsBuiltSnapshot(
            site=site,
            snapshot_date=datetime.utcnow(),
            created_by=snapshot_data.get('created_by', 'field_team'),
            poles=[AsBuiltPole(**p) for p in snapshot_data.get('poles', [])],
            connections=[AsBuiltConnection(**c) for c in snapshot_data.get('connections', [])],
            conductors=[AsBuiltConductor(**c) for c in snapshot_data.get('conductors', [])],
            metadata=snapshot_data.get('metadata', {})
        )
        
        # Store snapshot
        if site not in as_built_storage:
            as_built_storage[site] = []
        as_built_storage[site].append(snapshot.dict())
        
        # Process comparison with planned
        tracker = AsBuiltTracker(network_storage[site])
        comparison = tracker.process_as_built_snapshot(snapshot)
        
        return JSONResponse(content={
            "success": True,
            "message": f"As-built snapshot created for {site}",
            "snapshot_id": len(as_built_storage[site]) - 1,
            "summary": {
                "poles": len(snapshot.poles),
                "connections": len(snapshot.connections),
                "conductors": len(snapshot.conductors),
                "overall_progress": round(comparison.overall_progress, 1)
            }
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/as-built/{site}/snapshots")
async def get_as_built_snapshots(site: str):
    """
    Get all as-built snapshots for a site
    """
    try:
        if site not in as_built_storage:
            return JSONResponse(content={
                "success": True,
                "site": site,
                "snapshots": []
            })
        
        snapshots = []
        for idx, snapshot in enumerate(as_built_storage[site]):
            snapshots.append({
                "id": idx,
                "date": snapshot['snapshot_date'],
                "created_by": snapshot['created_by'],
                "poles": len(snapshot.get('poles', [])),
                "connections": len(snapshot.get('connections', [])),
                "conductors": len(snapshot.get('conductors', []))
            })
        
        return JSONResponse(content={
            "success": True,
            "site": site,
            "snapshots": snapshots
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/as-built/{site}/comparison")
async def compare_as_built_with_planned(
    site: str,
    snapshot_id: int = -1,
    threshold_meters: float = 10
):
    """
    Compare as-built snapshot with planned network
    Use snapshot_id=-1 for latest snapshot
    """
    try:
        if site not in network_storage:
            raise HTTPException(status_code=404, detail=f"Site {site} not found")
        
        if site not in as_built_storage or not as_built_storage[site]:
            raise HTTPException(status_code=404, detail=f"No as-built snapshots found for {site}")
        
        # Get snapshot
        snapshot_data = as_built_storage[site][snapshot_id]
        snapshot = AsBuiltSnapshot(**snapshot_data)
        
        # Process comparison
        tracker = AsBuiltTracker(network_storage[site])
        comparison = tracker.process_as_built_snapshot(snapshot, threshold_meters)
        report = tracker.generate_progress_report(comparison)
        
        return JSONResponse(content={
            "success": True,
            "report": report
        })
        
    except IndexError:
        raise HTTPException(status_code=404, detail=f"Snapshot {snapshot_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/as-built/{site}/update-progress")
async def update_construction_progress(
    site: str,
    updates: Dict[str, Any] = Body(...)
):
    """
    Update construction progress with incremental field data
    """
    try:
        if site not in network_storage:
            raise HTTPException(status_code=404, detail=f"Site {site} not found")
        
        # Get or create latest snapshot
        if site not in as_built_storage:
            as_built_storage[site] = []
        
        if as_built_storage[site]:
            # Start from latest snapshot
            latest = as_built_storage[site][-1].copy()
        else:
            # Start fresh
            latest = {
                'site': site,
                'snapshot_date': datetime.utcnow().isoformat(),
                'created_by': updates.get('updated_by', 'field_team'),
                'poles': [],
                'connections': [],
                'conductors': [],
                'metadata': {}
            }
        
        # Apply updates
        if 'poles' in updates:
            existing_poles = {p['pole_id']: p for p in latest['poles']}
            for pole_update in updates['poles']:
                pole_id = pole_update['pole_id']
                if pole_id in existing_poles:
                    existing_poles[pole_id].update(pole_update)
                else:
                    existing_poles[pole_id] = pole_update
            latest['poles'] = list(existing_poles.values())
        
        if 'connections' in updates:
            existing_conns = {c['connection_id']: c for c in latest['connections']}
            for conn_update in updates['connections']:
                conn_id = conn_update['connection_id']
                if conn_id in existing_conns:
                    existing_conns[conn_id].update(conn_update)
                else:
                    existing_conns[conn_id] = conn_update
            latest['connections'] = list(existing_conns.values())
        
        if 'conductors' in updates:
            existing_conds = {c['conductor_id']: c for c in latest['conductors']}
            for cond_update in updates['conductors']:
                cond_id = cond_update['conductor_id']
                if cond_id in existing_conds:
                    existing_conds[cond_id].update(cond_update)
                else:
                    existing_conds[cond_id] = cond_update
            latest['conductors'] = list(existing_conds.values())
        
        # Update metadata
        latest['snapshot_date'] = datetime.utcnow().isoformat()
        latest['created_by'] = updates.get('updated_by', latest['created_by'])
        
        # Store updated snapshot
        as_built_storage[site].append(latest)
        
        return JSONResponse(content={
            "success": True,
            "message": "Construction progress updated",
            "snapshot_id": len(as_built_storage[site]) - 1,
            "summary": {
                "poles": len(latest['poles']),
                "connections": len(latest['connections']),
                "conductors": len(latest['conductors'])
            }
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/as-built/{site}/progress-report")
async def get_progress_report(site: str):
    """
    Get detailed construction progress report
    """
    try:
        if site not in network_storage:
            raise HTTPException(status_code=404, detail=f"Site {site} not found")
        
        if site not in as_built_storage or not as_built_storage[site]:
            # No as-built data yet
            planned_data = network_storage[site]
            return JSONResponse(content={
                "success": True,
                "site": site,
                "report": {
                    "overall_progress": 0,
                    "planned": {
                        "poles": len(planned_data.get('poles', [])),
                        "connections": len(planned_data.get('connections', [])),
                        "conductors": len(planned_data.get('conductors', [])),
                        "length_km": sum(c.get('length', 0) for c in planned_data.get('conductors', [])) / 1000
                    },
                    "built": {
                        "poles": 0,
                        "connections": 0,
                        "conductors": 0,
                        "length_km": 0
                    },
                    "status_summary": {
                        "poles_by_status": {},
                        "connections_by_status": {},
                        "conductors_by_status": {}
                    }
                }
            })
        
        # Get latest snapshot
        latest_snapshot = AsBuiltSnapshot(**as_built_storage[site][-1])
        
        # Process comparison
        tracker = AsBuiltTracker(network_storage[site])
        comparison = tracker.process_as_built_snapshot(latest_snapshot)
        report = tracker.generate_progress_report(comparison)
        
        # Add status code summaries
        pole_status = {}
        for pole in latest_snapshot.poles:
            st_code = pole.st_code_1 or 0
            pole_status[st_code] = pole_status.get(st_code, 0) + 1
        
        conn_status = {}
        for conn in latest_snapshot.connections:
            st_code = conn.st_code_3 or 0
            conn_status[st_code] = conn_status.get(st_code, 0) + 1
        
        cond_status = {}
        for cond in latest_snapshot.conductors:
            st_code = cond.st_code_4 or 0
            cond_status[st_code] = cond_status.get(st_code, 0) + 1
        
        report['status_summary'] = {
            'poles_by_status': pole_status,
            'connections_by_status': conn_status,
            'conductors_by_status': cond_status
        }
        
        return JSONResponse(content={
            "success": True,
            "site": site,
            "report": report
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/as-built/{site}/export")
async def export_as_built_report(site: str, format: str = "excel"):
    """
    Export as-built comparison report
    """
    try:
        if site not in network_storage:
            raise HTTPException(status_code=404, detail=f"Site {site} not found")
        
        if site not in as_built_storage or not as_built_storage[site]:
            raise HTTPException(status_code=404, detail=f"No as-built data for {site}")
        
        # Get latest snapshot and comparison
        latest_snapshot = AsBuiltSnapshot(**as_built_storage[site][-1])
        tracker = AsBuiltTracker(network_storage[site])
        comparison = tracker.process_as_built_snapshot(latest_snapshot)
        
        if format == "excel":
            # Create Excel file
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Summary sheet
                summary_data = {
                    'Metric': ['Overall Progress', 'Poles Progress', 'Conductors Progress', 'Connections Progress'],
                    'Percentage': [
                        comparison.overall_progress,
                        comparison.pole_progress,
                        comparison.conductor_progress,
                        comparison.connection_progress
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Poles sheet
                if latest_snapshot.poles:
                    poles_data = [p.dict() for p in latest_snapshot.poles]
                    poles_df = pd.DataFrame(poles_data)
                    poles_df.to_excel(writer, sheet_name='As-Built Poles', index=False)
                
                # Conductors sheet
                if latest_snapshot.conductors:
                    conds_data = [c.dict() for c in latest_snapshot.conductors]
                    conds_df = pd.DataFrame(conds_data)
                    conds_df.to_excel(writer, sheet_name='As-Built Conductors', index=False)
                
                # Connections sheet
                if latest_snapshot.connections:
                    conns_data = [c.dict() for c in latest_snapshot.connections]
                    conns_df = pd.DataFrame(conns_data)
                    conns_df.to_excel(writer, sheet_name='As-Built Connections', index=False)
                
                # Differences sheet
                if comparison.pole_differences or comparison.conductor_differences or comparison.connection_differences:
                    all_diffs = []
                    for diff in comparison.pole_differences:
                        diff['element_type'] = 'pole'
                        all_diffs.append(diff)
                    for diff in comparison.conductor_differences:
                        diff['element_type'] = 'conductor'
                        all_diffs.append(diff)
                    for diff in comparison.connection_differences:
                        diff['element_type'] = 'connection'
                        all_diffs.append(diff)
                    
                    diffs_df = pd.DataFrame(all_diffs)
                    diffs_df.to_excel(writer, sheet_name='Differences', index=False)
            
            output.seek(0)
            filename = f"{site}_as_built_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            return StreamingResponse(
                io.BytesIO(output.read()),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            # Return JSON
            report = tracker.generate_progress_report(comparison)
            return JSONResponse(content={
                "success": True,
                "site": site,
                "report": report,
                "snapshot": latest_snapshot.dict()
            })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
