# External References

## Related Projects

### uGridPREDICT
- **Location**: `/Users/mattmso/Projects/uGridPREDICT`
- **Purpose**: Network planning and prediction tool
- **Integration**: Shares data models and calculation engines

## Data Sources

### Clarifying Questions
Located in uGridPREDICT project:
- `/Users/mattmso/Projects/uGridPREDICT/clarifying_questions.csv`
- `/Users/mattmso/Projects/uGridPREDICT/consolidated_clarifying_questions.csv`

These files contain:
- Field team feedback
- Implementation questions
- Technical clarifications
- Business rule definitions

### Standard Operating Procedures (SOP)

#### MGD045V03 - Status Code System
Defines the 5-tier status code system:
- **SC1**: Pole construction progress (0-9)
- **SC2**: Pole features (NA, SP, SI, KP, KI, TP, TI, TC, MP, MI, MC, EP, EI)
- **SC3**: Connection status (0-10)
- **SC4**: Conductor stringing (0-5)
- **SC5**: Generation elements (0-6)

## Excel Templates

### uGridPLAN Format
Standard Excel format with required sheets:
- **PoleClasses**: Pole inventory with coordinates and status
- **Connections**: Customer connection points
- **NetworkLines**: MV/LV conductor segments
- **DropLines**: Service drop connections
- **Transformers**: Transformer specifications

Example files:
- `/Updated_20250806_1518/Excel_Files/uGridPlan.xlsx`
- `/V03_uGridPREDICT_update.xlsx`

## GIS Data Formats

### Supported Formats
- **KML**: Google Earth visualization
- **Shapefile**: GIS industry standard
- **GeoJSON**: Web-friendly format

### Example Files
Located in `/Updated_20250806_1518/`:
- `GIS_Files/`: Shapefiles for network elements
- `KML_Files/`: KML exports for visualization

## Integration Points

### Google Apps Script
- **File**: `/uGridPREDICT_google_apps_script.gs.txt`
- **Purpose**: Google Sheets integration
- **Features**: Data validation, automated reports

### Database Schema
- **File**: `/integration.db`
- **Type**: SQLite (development)
- **Future**: PostgreSQL with PostGIS

## Technical Standards

### Coordinate Systems
- **Primary**: WGS84 (EPSG:4326)
- **Display**: Decimal degrees
- **Precision**: 6 decimal places

### Naming Conventions
- **Poles**: Site prefix + number (e.g., "KET001")
- **Connections**: Site + number + household (e.g., "KET 2246 HH1")
- **Conductors**: Auto-generated IDs

### Data Validation Rules
- Latitude: -90 to 90
- Longitude: -180 to 180
- Status codes: Per MGD045V03 SOP
- Voltage levels: MV (19kV), LV (400V)

## Business Rules

### Network Topology
- Poles can have multiple connections
- Conductors connect two nodes
- Transformers mount on poles
- Customer connections link to poles

### Status Progression
- Elements progress through defined status codes
- Status changes trigger validation
- Historical tracking maintained

## External APIs

### Mapping Services
- OpenStreetMap tiles for base maps
- Mapbox for satellite imagery (optional)
- Google Maps API for geocoding (optional)

### Weather Data
- For load calculations (future)
- Historical patterns for planning

## Documentation Links

### Development Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Leaflet Documentation](https://leafletjs.com/)
- [React Documentation](https://react.dev/)

### Standards
- [GeoJSON Specification](https://geojson.org/)
- [KML Reference](https://developers.google.com/kml)
- [PostGIS Documentation](https://postgis.net/)

## Contact Information

### Development Team
- Repository: GitHub (private)
- Issues: GitHub Issues
- Support: Development team Slack

### Field Teams
- Feedback via clarifying questions CSV
- Regular sync meetings
- Training materials available

## Version History

### Data Model Versions
- V1: Initial desktop format
- V2: Added status codes
- V3: Web platform migration

### API Versions
- v1: Current REST API
- v2: Planned GraphQL support

## Compliance

### Standards
- IEC 60038: Voltage standards
- IEEE 1547: Interconnection standards
- Local electrical codes

### Data Protection
- GDPR compliance for EU projects
- Local data residency requirements
- Encryption for sensitive data
