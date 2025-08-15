# API Reference

## Base URL
- Development: `http://localhost:8000`
- Production: `https://api.1pwr-grid.com` (future)

## Authentication
Currently no authentication required (MVP phase). Will add JWT tokens in production.

## Endpoints

### Network Data Management

#### Upload Excel File
```http
POST /api/upload/excel
```

**Request:**
- Content-Type: `multipart/form-data`
- Body: Excel file (uGridPLAN format)

**Response:**
```json
{
  "success": true,
  "message": "Successfully imported network data",
  "site": "KET",
  "stats": {
    "poles": 1575,
    "connections": 1280,
    "conductors": 2810,
    "transformers": 48
  }
}
```

#### Get Network Data
```http
GET /api/network/{site}
```

**Parameters:**
- `site` (string): Site identifier (e.g., "KET", "UGRIDPLAN")

**Response:**
```json
{
  "site": "KET",
  "data": {
    "poles": [...],
    "connections": [...],
    "conductors": [...],
    "transformers": [...]
  },
  "stats": {
    "total_poles": 1575,
    "total_connections": 1280,
    "total_conductors": 2810,
    "total_transformers": 48
  }
}
```

### Calculations

#### Calculate Voltage Drop
```http
POST /api/calculate/voltage
```

**Request:**
```json
{
  "network_data": {},
  "load_scenario": "peak",
  "voltage_level": 19000
}
```

**Response:**
```json
{
  "results": {
    "max_voltage_drop": 6.8,
    "violations": [],
    "node_voltages": {}
  }
}
```

### Export

#### Export Network Report
```http
POST /api/export/network-report
```

**Request:**
```json
{
  "site": "KET",
  "include_voltage": true,
  "include_validation": true
}
```

**Response:**
- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- File download

#### Export Field Report
```http
POST /api/export/field-report
```

**Request:**
```json
{
  "site": "KET",
  "team_id": "team_1",
  "date_range": {
    "start": "2025-01-01",
    "end": "2025-01-31"
  }
}
```

### Element Management

#### Update Network Element
```http
PUT /api/network/{site}/element/{element_id}
```

**Request:**
```json
{
  "type": "pole",
  "updates": {
    "latitude": -29.1234,
    "longitude": 27.5678,
    "st_code_1": 7,
    "st_code_2": "SI"
  }
}
```

**Response:**
```json
{
  "success": true,
  "element": {
    "id": "KET001",
    "type": "pole",
    ...updated_fields
  }
}
```

#### Delete Network Element
```http
DELETE /api/network/{site}/element/{element_id}
```

**Parameters:**
- `site`: Site identifier
- `element_id`: Element ID to delete

**Response:**
```json
{
  "success": true,
  "message": "Element deleted successfully"
}
```

## Data Models

### Pole Object
```typescript
{
  pole_id: string;
  latitude: number;
  longitude: number;
  pole_type: string;
  pole_class?: string;
  st_code_1?: number;  // 0-9
  st_code_2?: string;  // NA, SP, SI, etc.
  status: 'as_designed' | 'planned' | 'installed';
}
```

### Connection Object
```typescript
{
  survey_id: string;
  latitude: number;
  longitude: number;
  customer_name?: string;
  connection_type?: string;
  st_code_3?: number;  // 0-10
  status: string;
}
```

### Conductor Object
```typescript
{
  conductor_id: string;
  from_pole: string;
  to_pole: string;
  conductor_type: string;
  length: number;
  st_code_4?: number;  // 0-5
  voltage_level: 'MV' | 'LV' | 'DROP';
}
```

### Transformer Object
```typescript
{
  transformer_id: string;
  pole_id: string;
  capacity: number;
  type: string;
  st_code_5?: number;  // 0-6
}
```

## Error Responses

### 400 Bad Request
```json
{
  "success": false,
  "error": "Invalid file format",
  "detail": "Expected Excel file with uGridPLAN sheets"
}
```

### 404 Not Found
```json
{
  "success": false,
  "error": "Site not found",
  "detail": "No data available for site: XYZ"
}
```

### 500 Internal Server Error
```json
{
  "success": false,
  "error": "Internal server error",
  "detail": "Error processing request"
}
```

## Status Codes Reference

### St_code_1 (Poles)
- 0: uGridNET output (default)
- 1: Updated planned location
- 2: Marked with label onsite
- 3: Consent withheld
- 4: Consented
- 5: Hard Rock
- 6: Excavated
- 7: Pole planted
- 8: Poletop dressed
- 9: Conductor attached

### St_code_2 (Pole Features)
- NA: None
- SP: Stay wires planned
- SI: Stay wires installed
- KP: Kicker pole planned
- KI: Kicker pole installed
- TP: Transformer planned
- TI: Transformer installed
- TC: Transformer commissioned
- MP: Meter planned
- MI: Meter installed
- MC: Meter commissioned
- EP: Earth planned
- EI: Earth installed

### St_code_3 (Connections)
- 0-2: Survey/planning stages
- 3-5: Contract/payment stages
- 6-8: Installation stages
- 9-10: Commissioning stages

### St_code_4 (Conductors)
- 0: Not strung
- 1-2: Preparation stages
- 3-5: Strung/installed stages

### St_code_5 (Generation)
- 0-2: Planning stages
- 3-4: Installation stages
- 5-6: Operational stages
