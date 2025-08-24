# 1PWR Grid Platform - Technical Specifications

## 1. System Overview

### 1.1 Purpose
Migrate and unify three legacy desktop tools (uGridNET, uGridPLAN, uGridPREDICT) into a modern web-based platform for 1PWR minigrid deployment management in Lesotho, Benin, and Zambia.

### 1.2 Core Requirements
1. **No feature loss** - MVP must retain ALL existing uGridPLAN functionality
2. **Voltage drop validation** - Core engineering calculations must be preserved  
3. **Excel/KML import/export** - Field teams depend on these formats
4. **Web-based** - Replace desktop tools with browser-based solution
5. **Configurable** - Site count, voltage levels, conductor specs must be user-editable

## 2. Functional Specifications

### 2.1 Authentication & Authorization
- **JWT-based authentication** with access and refresh tokens
- **Token storage** in localStorage
- **Auto-refresh** 1 minute before token expiry
- **Role-based access control** (Admin, Field User, Viewer)
- **Test accounts**:
  - admin / admin123
  - field_user / field123
  - viewer / viewer123

### 2.2 Data Import
- **Excel Import** (uGridPLAN format)
  - Parse Poles, Connections, Conductors sheets
  - Handle duplicate detection (connections appearing in poles sheet)
  - Support for legacy pickle files
- **KML Validation** - Cross-reference with ground truth
- **Automatic Data Cleaning**:
  - Fix missing cable sizes (default: AAC_35)
  - Remove orphaned connections
  - Resolve network connectivity issues
  - Handle invalid pole references

### 2.3 Network Visualization
- **Map Display** (Leaflet-based)
  - Interactive map with OpenStreetMap tiles
  - Zoom controls (range 10-20)
  - Pan and navigation controls
- **Network Elements**:
  - Poles: Circle markers (6px radius)
  - Connections: Square markers
  - Conductors: Polylines with status colors
  - Transformers: Special markers
- **Visual Styling**:
  - 50% transparency on all fills
  - Status-based coloring (MGD045V03 SOP compliant)
  - MV poles with black borders (identified by "_M" in ID)
  - Borderless connections and LV poles
- **Layer Ordering** (z-index control):
  - Connections (bottom)
  - LV poles
  - MV poles  
  - Lines (top)
- **Performance**:
  - Batch rendering (20 items for poles/connections, 10 for conductors)
  - Progressive rendering with 16ms frame time limit
  - Marker clustering with 200ms chunked loading
  - Progress bar for large datasets

### 2.4 Voltage Drop Calculations
- **Real-time calculation** via backend API
- **Visualization**:
  - Color gradient: Green (0-2%) → Yellow (4-6%) → Red (>8%)
  - Interactive tooltips with voltage values
  - Violation detection and highlighting
  - Toggle control with Zap icon
- **Thresholds**:
  - Maximum voltage drop: 7% (configurable)
  - Default load assumption: 2kW per connection

### 2.5 Network Validation
- **Topology Validation**:
  - Ensure radial network structure
  - Detect and remove cycles
  - Identify disconnected components
  - Validate conductor endpoints
- **Data Integrity Checks**:
  - Orphaned poles detection
  - Invalid conductor references
  - Duplicate ID detection
  - Missing required fields
- **Real-time validation panel** with filtering and search

### 2.6 Network Editing
- **Edit Operations**:
  - Add poles/connections
  - Move network elements
  - Delete elements with cascade handling
  - Update element properties
- **Edit Toolbar** positioning at left: 60px to avoid zoom control overlap
- **Undo/Redo functionality**

### 2.7 Data Export
- **Excel Export**:
  - Comprehensive network reports
  - Validation results included
  - Field team reports
  - Material takeoff reports
- **Format**: uGridPLAN compatible Excel files

### 2.8 As-Built Tracking
- **Status tracking** for network elements
- **Progress monitoring** by work package (WP1-8)
- **Field report integration**
- **Update from field data**

## 3. Technical Specifications

### 3.1 Architecture
- **Backend**: FastAPI (Python 3.10+)
- **Frontend**: Next.js 14, React 18, TypeScript
- **Database**: In-memory storage (PostgreSQL planned)
- **API**: RESTful with potential WebSocket support

### 3.2 API Endpoints
- `POST /api/auth/login` - User authentication
- `POST /api/auth/refresh` - Token refresh
- `GET /api/auth/me` - Current user info
- `POST /api/upload/excel` - Upload Excel file
- `GET /api/network/{site}` - Get network data
- `POST /api/calculate/voltage` - Calculate voltage drop
- `POST /api/export/excel/{site}` - Export Excel report
- `GET /api/network/{site}/validation` - Get validation results
- `PUT /api/network/{site}/element/{id}` - Update element

### 3.3 Data Models
- **Poles**: ID, coordinates, type (MV/LV), status, voltage
- **Connections**: ID, pole_id, coordinates, load, status
- **Conductors**: ID, from_pole, to_pole, cable_spec, length, status
- **Transformers**: ID, pole_id, rating, type

### 3.4 Conductor Types
- AAC_50, AAC_35, AAC_25, AAC_16
- ABC_50, ABC_35, ABC_25, ABC_16

### 3.5 Sites
11 configured sites including KET, UGRIDPLAN, etc.

## 4. User Interface Specifications

### 4.1 Layout
- **CSS Grid layout** with 256px fixed sidebar
- **Responsive design** for various screen sizes
- **Dark mode support**

### 4.2 Components
- **Dashboard** with site selector
- **Map View** with editing tools
- **Statistics Panel** with network metrics
- **Validation Panel** with error listings
- **Upload Component** with drag-drop support

### 4.3 Navigation
- **Sidebar navigation** with full height
- **View switching** (Map/Stats/Validation)
- **User menu** with logout option

## 5. Performance Requirements

### 5.1 Loading Times
- Initial page load: < 3 seconds
- Network data load: < 5 seconds for 5000 elements
- Map rendering: Progressive with 60fps target

### 5.2 Scalability
- Support 10,000+ network elements
- Handle concurrent users
- Efficient batch operations

## 6. Security Requirements

### 6.1 Authentication
- Secure JWT token handling
- HTTPS in production
- CORS configuration for API

### 6.2 Data Protection
- Input validation and sanitization
- SQL injection prevention (when DB implemented)
- XSS protection

## 7. Deployment Requirements

### 7.1 Development
- Frontend: Port 3000-3003 (auto-increment if busy)
- Backend: Port 8000

### 7.2 Production
- Docker containerization
- CI/CD pipeline
- Cloud deployment (AWS/Azure/GCP)

## 8. Testing Requirements

### 8.1 Test Coverage
- Unit tests for critical functions
- Integration tests for API endpoints
- E2E tests for user workflows

### 8.2 Test Data
- Sample Excel files in test_data/
- KET site data for validation

## 9. Documentation Requirements

### 9.1 Technical Documentation
- API documentation
- Architecture guide
- Development setup guide

### 9.2 User Documentation
- User manual
- Field team guides
- Training materials

## 10. Future Enhancements

### 10.1 Phase 2 Features
- Database persistence (PostgreSQL)
- Multi-user collaboration
- Real-time updates via WebSocket
- Advanced reporting

### 10.2 uGridPREDICT Integration  
- Resource allocation algorithms
- Progress prediction models
- Gantt chart generation
- Mode 1 (resource-driven) vs Mode 2 (target-driven)

### 10.3 Additional Calculations
- Transformer sizing validation
- Phase balancing algorithms  
- Cost calculations
- Advanced material takeoff reports

## 11. Implementation Discrepancies

### 11.1 API Endpoint Differences
**Note: These differences exist between the specification and current implementation. The implementation is working correctly.**

| Specification | Implementation | Status |
|--------------|----------------|--------|
| `POST /api/calculate/voltage` | `POST /api/voltage/{site}` | ✅ Working |
| `GET /api/network/{site}/validation` | `POST /api/validate/network` | ✅ Working |
| `PUT /api/network/{site}/element/{id}` | Multiple endpoints: | ✅ Working |
| | - `POST /api/network/poles/{site}` | |
| | - `PUT /api/network/poles/{site}/{pole_id}` | |
| | - `DELETE /api/network/poles/{site}/{pole_id}` | |
| | - `POST /api/network/connections/{site}` | |
| | - `DELETE /api/network/connections/{site}/{connection_id}` | |
| | - `POST /api/network/conductors/{site}` | |
| | - `PUT /api/network/conductors/{site}/{conductor_id}` | |
| | - `DELETE /api/network/conductors/{site}/{conductor_id}` | |
| | - `POST /api/network/conductors/{site}/{conductor_id}/split` | |

### 11.2 Additional Implemented Features
**These features exist in the implementation but not in the original specification:**

1. **As-Built Tracking** (Partially implemented)
   - `POST /api/as-built/{site}/snapshot`
   - `GET /api/as-built/{site}/snapshots`
   - `GET /api/as-built/{site}/comparison`
   - `POST /api/as-built/{site}/update-progress`
   - `GET /api/as-built/{site}/progress-report`
   - `GET /api/as-built/{site}/export`

2. **Material Takeoff**
   - `GET /api/material-takeoff/{site}`
   - `GET /api/material-takeoff/{site}/excel`
   - `GET /api/material-takeoff/{site}/summary`

3. **Additional Export Endpoints**
   - `POST /api/export/field-report`
   - `POST /api/export/network-report`
   - `POST /api/upload/pickle` (legacy support)

4. **Generation Site Management**
   - `POST /api/network/{site}/generation`

### 11.3 Recommendations
1. **Keep current implementation** - The API endpoints are functional and more granular than the specification
2. **Update frontend API calls** - Ensure frontend uses the actual implemented endpoints
3. **Document actual API** - Update API.md with the real endpoint structure
4. **Specification serves as high-level guide** - Use this document for understanding requirements, not exact implementation details
