# 1PWR Grid Platform

Unified web platform for 1PWR minigrid deployment tools, replacing desktop Python/Tkinter applications with a modern web-based solution.

## 🏗️ Architecture

This platform consolidates three tools:
- **uGridNET** - Network design (pre-construction)
- **uGridPLAN** - As-built tracking (during construction)
- **uGridPREDICT** - Resource allocation & progress prediction

## 📦 Modular Structure

```
1pwr-grid-platform/
├── core/                   # Shared core functionality
│   ├── models/            # Pydantic data models
│   ├── database/          # Database connections & migrations
│   └── validators/        # Shared validation logic
├── modules/               # Feature modules
│   ├── import_pipeline/   # Excel/data import
│   ├── network_engine/    # Network topology & calculations
│   ├── voltage_validation/# Voltage drop validation
│   ├── progress_tracking/ # Work package tracking
│   └── reporting/         # Report generation
├── api/                   # FastAPI backend
│   ├── routers/          # API endpoints
│   └── middleware/       # Auth & logging
├── web/                   # Next.js frontend
│   ├── components/       # React components
│   └── pages/           # Application pages
├── tests/                 # Test suites
│   ├── unit/            # Unit tests per module
│   └── integration/     # Integration tests
└── scripts/              # Utility scripts
    └── migration/       # Data migration tools
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+ with PostGIS
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/1pwr/1pwr-grid-platform.git
cd 1pwr-grid-platform
```

2. Set up Python environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up database:
```bash
createdb ugrid_platform
psql -d ugrid_platform -c "CREATE EXTENSION postgis;"
python scripts/migrate_database.py
```

4. Run tests:
```bash
pytest tests/unit/
```

## 📋 Development Guidelines

### Modular Development
Each module should:
1. Be independently testable
2. Have clear input/output contracts
3. Include comprehensive unit tests
4. Document all assumptions
5. Handle errors gracefully

### Git Workflow
- Feature branches: `feature/module-name`
- Bugfix branches: `bugfix/issue-description`
- Always test before merging
- Use conventional commits

### Testing Requirements
- Unit test coverage > 80%
- All validation logic must have tests
- Integration tests for critical paths
- Performance benchmarks for imports

## 🔧 Module Status

| Module | Status | Tests | Notes |
|--------|--------|-------|-------|
| Import Pipeline | 🟡 In Progress | 0% | Excel/CSV import |
| Network Engine | ⭕ Not Started | 0% | NetworkX integration |
| Voltage Validation | ⭕ Not Started | 0% | 7% threshold |
| Progress Tracking | ⭕ Not Started | 0% | WP calculations |
| Reporting | ⭕ Not Started | 0% | Excel generation |

## 📝 Configuration

Key parameters in `config.yaml`:
- `VOLTAGE_DROP_THRESHOLD`: 7% (configurable)
- `VOLTAGE_LEVELS`: [19000, 11000] (SWER vs 3-phase)
- `CONDUCTOR_TYPES`: Defined in database
- `PEAK_LOAD_SCENARIO`: Site-specific

## 🤝 Contributing

1. Check module status above
2. Pick a module to work on
3. Write tests first (TDD)
4. Implement functionality
5. Document changes
6. Submit PR with tests passing

## 📄 License

Proprietary - 1PWR Internal Use Only

## 🔗 Links

- [Architecture Document](docs/ARCHITECTURE.md)
- [API Specification](docs/API_SPEC.md)
- [Data Schema](docs/DATA_SCHEMA.md)
