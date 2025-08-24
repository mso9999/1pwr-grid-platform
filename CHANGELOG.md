# Changelog

## [2024-08-24] - Add Pole Dialog Implementation & API Fix

### Added
- **Add Pole Dialog**: Complete pole creation form with all required fields
  - Pole ID (auto-generated if empty)
  - Pole Type dropdown (POLE, STAY, ANCHOR, etc.)
  - Pole Class dropdown (LV, MV, HV)
  - Status Code 1 with descriptions (0-9 construction progress)
  - Status Code 2 with descriptions (NA, SP, SI, KP, etc.)
  - Angle Class with degree ranges (0-15, 15-30, 30-45, 45-60, 60-90)
  - Notes field for additional information

### Changed
- **uGridPLAN Compatibility**: Updated angle_class to use degree-based classification
  - Changed from T/A/D/I system to degree ranges (0-15, 15-30, 30-45, 45-60, 60-90)
  - Updated backend PoleCreate model default from "T" to "0-15"
  - Maintains backwards compatibility with original uGridPLAN AngleClass column
- **API Data Types**: Fixed st_code_2 field type mismatch
  - Changed backend from integer to string to match uGridPLAN format
  - Updated frontend form data types for consistency

### Fixed
- **Pole Creation API**: Resolved 422 Unprocessable Entity error
  - Fixed data type mismatch between frontend and backend for st_code_2 field
  - Backend now accepts string status codes (NA, SP, SI, etc.) as per uGridPLAN
  - Added enhanced error logging for better debugging
- **Modal Dialog Issues**: Replaced Shadcn Dialog with custom modal implementation
  - Fixed z-index conflicts preventing dialog visibility
  - Added inline styles and DOM verification
  - Resolved infinite render loops from console.log statements
- **Map Click Handler**: Fixed premature removal of click handlers during mode changes
- **TypeScript Errors**: Corrected form data types and state management

## [2024-08-22] - Map Rendering and Authentication Fixes

### Fixed
- **Map Rendering Issues**
  - Fixed corrupted code in `ClientMap.tsx` that prevented proper rendering
  - Increased pole icon radius from 3px to 6px for better visibility
  - Applied 50% transparency to all map element fills for visual consistency
  - Fixed dropline rendering by ensuring connections exist in network data
  - Corrected conductor batch rendering to respective layer groups

### Added
- **Test Data Generation**
  - Created `add_test_connections.py` script to inject sample connections
  - Added 52 test connections near poles with GPS coordinates
  - Added 30 dropline conductors linking poles to connections
  - Script automatically updates KET network data JSON file

### Enhanced
- **Authentication System**
  - Verified JWT-based authentication with access/refresh tokens
  - Confirmed automatic token refresh 1 minute before expiry
  - Validated login flow with test accounts (admin/admin123, field_user/field123, viewer/viewer123)
  - Protected routes redirect to login when unauthenticated

### Technical Details
- **Frontend**: React/Next.js with Leaflet map rendering
- **Backend**: FastAPI with JWT authentication
- **Data Format**: Fixed field name mismatches (pole_id vs id, from_pole vs from)
- **Map Layers**: Separate panes for MV poles, LV poles, connections, and droplines
- **Performance**: Batch rendering with progress feedback for large datasets

### Test Accounts
- admin / admin123 (Administrator role)
- field_user / field123 (Field user role)  
- viewer / viewer123 (Viewer role)
