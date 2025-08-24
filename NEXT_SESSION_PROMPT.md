# System Prompt for uGridPLAN Migration Continuation

## Current Status
You are continuing work on migrating the desktop uGridPLAN application to a web platform. Currently only **7% of features are verified working** (Excel import/export and network visualization). Code exists for several other features but they are NOT functional or tested.

## Key Context Documents
1. **UGRIDPLAN_MIGRATION_STATUS.md** - Current migration status (7% complete)
2. **specifications.md** - Visual specs and requirements
3. **DEVELOPER_HANDOVER.md** - Original architecture notes
4. **SESSION_SUMMARY_240824.md** - Latest session work (map rendering fixes)

## Verified Working Features
- Excel import/export (backend/routes/material_takeoff.py)
- Network visualization (web-app/src/components/map/ClientMap.tsx)
- Map styling: MV=blue lines, LV=green lines, Drop=orange lines
- Pole borders: MV=black border, LV=no border

## Critical Code Files
### Frontend
- `/web-app/src/components/map/ClientMap.tsx` - Main map component (1400+ lines)
- `/web-app/src/components/map/MapEditToolbar.tsx` - Editing tools
- `/web-app/src/app/page.tsx` - Dashboard entry point

### Backend
- `/backend/main.py` - FastAPI server
- `/backend/routes/network_edit.py` - CRUD endpoints (untested)
- `/backend/utils/voltage_calculator.py` - Voltage drop (untested)
- `/backend/routes/auth.py` - Authentication (untested)

## Recent Git Commits
```
10cfa0a1 - Correct migration status to reflect actual verified features
822bd154 - Fix Leaflet map rendering: remove clustering, fix layer order
3f8dba95 - Previous session work
```

## Priority Tasks to Complete Migration

### IMMEDIATE (Test Existing Code)
1. **Test Network Editing CRUD**
   - Verify add/delete poles works
   - Test conductor creation/deletion
   - Check incremental updates without reload
   - Files: MapEditToolbar.tsx, network_edit.py

2. **Test Authentication Flow**
   - Verify login/logout works
   - Test role-based permissions
   - Check JWT token handling
   - Files: auth.py, AuthContext.tsx

3. **Test Voltage Drop**
   - Verify backend calculations
   - Add frontend visualization overlay
   - Test with KET site data
   - Files: voltage_calculator.py, VoltageOverlay.tsx

### NEXT PRIORITY (Implement Missing)
1. **Add Search Functionality**
   - Search poles/connections by ID
   - Frontend search component
   - Backend search API

2. **Add Database Persistence**
   - PostgreSQL schema design
   - Replace in-memory storage
   - Migration scripts

3. **Fix Material Reports**
   - Frontend integration
   - Excel export verification

## Test Data Location
- Excel files: `/Users/mattmso/Projects/uGridPREDICT/Updated_20250806_1518/Excel_Files/uGridPlan.xlsx`
- Sites: KET (1575 poles), SHG

## Development Environment
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Node/npm for frontend, Python/FastAPI for backend

## Testing Approach
1. Start with manual testing of existing code
2. Document what actually works vs what's broken
3. Fix broken features before adding new ones
4. Update UGRIDPLAN_MIGRATION_STATUS.md as features are verified

## Key Issues from Last Session
- Fixed line colors (was using SC4 status colors instead of line type)
- Fixed LV pole borders (was incorrectly showing borders)
- Removed marker clustering (was showing numbered circles)
- Layer ordering fixed (connections→poles→lines)

## Success Criteria
Move from 7% to at least 50% verified working features by:
- Getting CRUD operations fully functional
- Verifying authentication works end-to-end
- Adding voltage drop visualization
- Implementing search
- Adding database persistence

Remember: Code existing ≠ Feature working. Test everything!
