# Changelog

## [2024-08-24] - Add Pole Dialog and uGridPLAN Compatibility

### Added
- **Add Pole Dialog**: Fully functional pole creation modal with all required fields
- **uGridPLAN Backwards Compatibility**: Implemented proper angle class system using degree ranges (0-15°, 15-30°, etc.)
- **Status Code Descriptions**: User-friendly descriptions for all status codes in form dropdowns
- **Custom Modal System**: Replaced problematic Shadcn Dialog with custom modal for reliable rendering

### Fixed
- **Pole Dialog Visibility**: Resolved z-index and rendering issues preventing modal from appearing
- **Infinite Render Loop**: Eliminated performance issues caused by inline function references
- **Map Click Handler**: Fixed premature removal of click handlers during pole creation workflow
- **TypeScript Errors**: Corrected form data types to match backend API requirements
- **Angle Class System**: Replaced incorrect T/A/D/I system with actual uGridPLAN degree-based classification

### Changed
- **Backend API**: Updated default angle_class from "T" to "0-15" for uGridPLAN compatibility
- **Specifications**: Updated angle class documentation to reflect degree-based system
- **Form Validation**: Enhanced pole creation form with proper field validation and descriptions

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
