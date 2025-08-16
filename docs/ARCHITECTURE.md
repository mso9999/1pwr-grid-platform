# Architecture Guide

## System Overview

The 1PWR Grid Platform is a modern web application that consolidates three legacy desktop tools into a unified platform for minigrid deployment and management.

## Architecture Principles

- **Modular Design**: Separate concerns into independent modules
- **API-First**: RESTful API backend with clear contracts
- **Real-time Updates**: WebSocket support for live data
- **Scalable**: Ready for multi-site, multi-user deployment
- **Maintainable**: Clean code with comprehensive testing

## System Components

### Backend Services

- **FastAPI Application** (`backend/main.py`)
  - REST API endpoints
  - File upload handling
  - Network data processing
  - Voltage calculations
  - Export generation
  - Network validation endpoint

- **Validators** (`backend/validators/`)
  - NetworkValidator: Validates network topology and data integrity

- **Utilities** (`backend/utils/`)
  - ExcelImporter: Parses uGridPLAN Excel files
  - VoltageCalculator: Calculates voltage drops
  - ReportExporter: Generates Excel reports

### Frontend (Next.js)
- **Location**: `/web-app/`
- **Port**: 3001
- **Responsibilities**:
  - User interface
  - Interactive map visualization (Leaflet)
  - Real-time data display
  - File upload/download

### Core Modules

#### Import Pipeline
- Excel file parsing (uGridPLAN format)
- KML validation
- Data cleaning and normalization
- Reference matching

#### Network Engine
- Voltage drop calculations
- Network topology validation
- Conductor sizing
- Transformer placement

#### Export Pipeline
- Excel report generation
- Field team reports
- Network analysis exports
- KML export

## Data Flow

```
Excel Upload → Import Pipeline → Data Cleaning → Backend Storage
                                                         ↓
Frontend Request ← API Response ← Network Engine ← Validated Data
```

## Technology Stack

### Backend
- **Framework**: FastAPI 0.104+
- **Language**: Python 3.10+
- **Libraries**:
  - openpyxl (Excel processing)
  - NetworkX (graph algorithms)
  - NumPy (calculations)
  - Pydantic (data validation)

### Frontend
- **Framework**: Next.js 14
- **Language**: TypeScript
- **Libraries**:
  - React 18
  - Leaflet (mapping)
  - Tailwind CSS (styling)
  - Radix UI (components)

## API Design

### RESTful Endpoints
- `POST /api/upload/excel` - Upload Excel file
- `GET /api/network/{site}` - Get network data
- `POST /api/calculate/voltage` - Calculate voltage drop
- `POST /api/export/excel/{site}` - Export Excel report
- `PUT /api/network/{site}/element/{id}` - Update element

### Response Format
```json
{
  "success": true,
  "data": {},
  "stats": {},
  "site": "KET"
}
```

## Security Considerations

- CORS configuration for API access
- Input validation on all endpoints
- File type verification for uploads
- Rate limiting for API calls
- Secure file handling

## Performance Optimization

- Lazy loading for map elements
- Pagination for large datasets
- Caching for calculated values
- Efficient graph algorithms
- WebWorkers for heavy calculations

## Deployment Architecture

### Development
- Local development servers
- Hot module replacement
- Debug logging enabled

### Production
- Docker containerization
- Nginx reverse proxy
- PostgreSQL database
- Redis caching layer
- Load balancing support

## Database Schema (Future)

### Core Tables
- `sites` - Site information
- `poles` - Pole inventory
- `connections` - Customer connections
- `conductors` - Line segments
- `transformers` - Transformer assets
- `users` - User accounts
- `projects` - Project management

## Scalability Considerations

- Microservices architecture ready
- Horizontal scaling support
- Database sharding capability
- CDN integration for assets
- Queue-based processing

## Monitoring and Logging

- Structured logging (JSON)
- Error tracking (Sentry ready)
- Performance monitoring
- API metrics collection
- Health check endpoints
