# Development Guide

## Getting Started

### Prerequisites
- Python 3.10 or higher
- Node.js 18 or higher
- Git
- VS Code or similar IDE

### Initial Setup

1. **Clone the repository**
```bash
git clone https://github.com/1pwr/1pwr-grid-platform.git
cd 1pwr-grid-platform
```

2. **Backend setup**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
```

3. **Frontend setup**
```bash
cd web-app
npm install
```

### Running the Application

Start both servers in separate terminals:

```bash
# Terminal 1 - Backend (port 8000)
cd backend
python main.py

# Terminal 2 - Frontend (port 3001)
cd web-app
npm run dev
```

Access the application at http://localhost:3001

## Development Workflow

### Code Structure

```
1pwr-grid-platform/
├── backend/               # FastAPI backend
│   ├── main.py           # API endpoints
│   └── requirements.txt   # Python dependencies
├── modules/              # Core business logic
│   ├── import_pipeline/  # Data import modules
│   ├── network_engine/   # Calculations
│   ├── data_cleaning/    # Data validation
│   └── export_pipeline/  # Export functionality
├── web-app/              # Next.js frontend
│   └── src/
│       ├── app/         # Main application
│       ├── components/  # React components
│       └── lib/         # Utilities
└── docs/                 # Documentation
```

### Git Workflow

1. **Create feature branch**
```bash
git checkout -b feature/your-feature-name
```

2. **Make changes and commit**
```bash
git add .
git commit -m "feat: add new feature"
```

3. **Push and create PR**
```bash
git push origin feature/your-feature-name
```

### Commit Convention

Use conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `style:` Formatting
- `refactor:` Code restructuring
- `test:` Tests
- `chore:` Maintenance

## Testing

### Backend Testing
```bash
# Run all tests
pytest

# Run specific module
pytest modules/import_pipeline/

# Run with coverage
pytest --cov=modules
```

### Frontend Testing
```bash
cd web-app
npm test
npm run test:coverage
```

### Manual Testing

1. **Test Excel Import**
   - Use sample file: `test_data/uGridPlan.xlsx`
   - Upload via UI or API
   - Verify data appears on map

2. **Test Map Visualization**
   - Check all element types render
   - Verify status colors
   - Test layer toggles
   - Confirm popups work

3. **Test Voltage Calculations**
   - Enable voltage overlay
   - Check color gradients
   - Verify violation detection

## Common Tasks

### Adding a New API Endpoint

1. Add route in `backend/main.py`:
```python
@app.get("/api/your-endpoint")
async def your_endpoint():
    return {"data": "value"}
```

2. Add API client method in `web-app/src/lib/api.ts`:
```typescript
export async function yourEndpoint() {
  return fetch(`${API_URL}/api/your-endpoint`)
}
```

### Adding a New React Component

1. Create component file:
```typescript
// web-app/src/components/YourComponent.tsx
export function YourComponent() {
  return <div>Component</div>
}
```

2. Import and use:
```typescript
import { YourComponent } from '@/components/YourComponent'
```

### Updating Status Codes

Status codes are defined in:
- Backend: Check Excel import logic
- Frontend: `web-app/src/utils/statusCodes.ts`

## Debugging

### Backend Debugging

1. **Enable debug logging**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. **Use debugger**
```python
import pdb; pdb.set_trace()
```

### Frontend Debugging

1. **Browser DevTools**
   - Console for errors
   - Network tab for API calls
   - React DevTools extension

2. **Add debug logs**
```typescript
console.log('Debug:', variable)
```

## Performance Optimization

### Backend
- Use async/await for I/O operations
- Implement caching for calculations
- Optimize database queries
- Use pagination for large datasets

### Frontend
- Lazy load components
- Implement virtual scrolling
- Use React.memo for expensive renders
- Optimize map rendering with clustering

## Troubleshooting

### Common Issues

1. **Map not rendering**
   - Check browser console for errors
   - Verify backend is running (port 8000)
   - Ensure network data is loaded

2. **Excel upload fails**
   - Verify file format (uGridPLAN)
   - Check required sheets exist
   - Review backend logs for errors

3. **CORS errors**
   - Ensure backend CORS is configured
   - Check API URL in frontend

### Environment Issues

1. **Python dependencies**
```bash
pip install --upgrade pip
pip install -r backend/requirements.txt --force-reinstall
```

2. **Node dependencies**
```bash
cd web-app
rm -rf node_modules package-lock.json
npm install
```

## Code Quality

### Linting

**Python:**
```bash
# Install
pip install black flake8

# Run
black modules/ backend/
flake8 modules/ backend/
```

**TypeScript:**
```bash
cd web-app
npm run lint
npm run lint:fix
```

### Type Checking

**Python:**
```bash
pip install mypy
mypy modules/ backend/
```

**TypeScript:**
```bash
cd web-app
npm run type-check
```

## Deployment Preparation

### Build for Production

**Backend:**
```bash
# Use production server
pip install gunicorn
gunicorn backend.main:app
```

**Frontend:**
```bash
cd web-app
npm run build
npm start
```

### Environment Variables

Create `.env` files:

**Backend (.env):**
```
DATABASE_URL=postgresql://...
SECRET_KEY=your-secret-key
ENVIRONMENT=production
```

**Frontend (.env.local):**
```
NEXT_PUBLIC_API_URL=https://api.1pwr-grid.com
```

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Leaflet Documentation](https://leafletjs.com/)
- [React Documentation](https://react.dev/)

## Support

For questions or issues:
1. Check existing GitHub issues
2. Review this documentation
3. Contact the development team
