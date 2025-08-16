# 1PWR Grid Platform

Modern web-based platform for 1PWR minigrid deployment, consolidating uGridNET, uGridPLAN, and uGridPREDICT tools.

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Git

### Installation

```bash
# Backend setup
git clone https://github.com/1pwr/1pwr-grid-platform.git
cd 1pwr-grid-platform
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt

# Frontend setup
cd web-app
npm install
```

### Running the Application

```bash
# Terminal 1 - Backend (port 8000)
cd backend
python main.py

# Terminal 2 - Frontend (port 3001)
cd web-app
npm run dev
```

Access the application at http://localhost:3001

## 📊 Current Status

### ✅ Completed Features
- Excel file upload and parsing (uGridPLAN format with fixed column mappings)
- Interactive Leaflet map with network visualization
- Network validation system (orphaned poles, invalid conductors, duplicate IDs, connectivity)
- Real-time ValidationPanel with filtering and search
- Voltage drop calculation and overlay
- Excel export with comprehensive reports (including validation results)
- Real-time network data API with validation endpoint
- Status-based coloring for poles, connections, conductors (MGD045V03 SOP compliant)

### 🚧 In Progress
- Network element editing (add/move/delete)
- User authentication and permissions
- As-built progress tracking
- Work package management

### 📈 Migration Progress
| Component | Status | Notes |
|-----------|--------|-------|
| Excel Import | ✅ 100% | Full uGridPLAN format support |
| Map Display | ✅ 80% | Missing editing tools |
| Voltage Calculations | ✅ 100% | Backend + frontend visualization |
| Excel Export | ✅ 100% | Network and field reports |
| Network Editing | 🚧 20% | Basic structure in place |
| User Management | ❌ 0% | Not started |
| Database | ❌ 0% | Using in-memory storage |

## 🏗️ Project Structure

```
1pwr-grid-platform/
├── backend/                # FastAPI backend
│   ├── main.py            # API endpoints
│   └── requirements.txt    # Python dependencies
├── modules/               # Core business logic
│   ├── import_pipeline/   # Excel/KML importers
│   ├── network_engine/    # Network calculations
│   ├── data_cleaning/     # Data validation
│   └── export_pipeline/   # Excel export
├── web-app/               # Next.js frontend
│   ├── src/
│   │   ├── app/          # Main application
│   │   ├── components/   # React components
│   │   └── lib/          # API client, utilities
│   └── package.json
├── docs/                  # Documentation
│   ├── ARCHITECTURE.md    # System architecture
│   ├── API.md            # API documentation
│   └── DEPLOYMENT.md     # Deployment guide
└── test_data/            # Sample Excel/KML files
```

## 📚 Documentation

- **[Architecture Guide](docs/ARCHITECTURE.md)** - System design and technical decisions
- **[API Reference](docs/API.md)** - Backend API endpoints and usage
- **[Development Guide](docs/DEVELOPMENT.md)** - Setup and contribution guidelines
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment instructions
- **[Migration Status](docs/MIGRATION_STATUS.md)** - Progress tracking from desktop tools

## 🔗 External References

- **[Clarifying Questions](../uGridPREDICT/clarifying_questions.csv)** - Business requirements Q&A
- **[Field Team Feedback](docs/FIELD_TEAM_FEEDBACK.md)** - User requirements from field teams
- **SOP Documentation** - Standard Operating Procedures (MGD045V03)

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python 3.10+)
- **Frontend**: Next.js 14, React 18, TypeScript
- **Mapping**: Leaflet with OpenStreetMap
- **UI**: Tailwind CSS, Radix UI, Lucide Icons
- **Data**: Excel (openpyxl), NetworkX, NumPy

## 🤝 Contributing

See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed contribution guidelines.

### Quick Guidelines
1. Create feature branch from `main`
2. Write tests for new functionality
3. Ensure all tests pass
4. Update documentation
5. Submit pull request

## 📄 License

Proprietary - 1PWR Internal Use Only

## 👥 Team

Developed by 1PWR engineering team for minigrid deployment in Lesotho, Benin, and Zambia.

## 📞 Support

For issues or questions:
- Create a GitHub issue
- Contact the development team
- Check the documentation
