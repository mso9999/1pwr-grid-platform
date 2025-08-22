# 1PWR Grid Platform UI Style Guide

## Purpose
Establish a consistent, accessible, and efficient UI for the 1PWR Grid Platform - a web-based engineering design tool that performs CRUD operations on electricity network topology elements (substations, feeders, transformers, poles, conductors, switches, meters, etc.).

## Audience
- Frontend Engineers
- UI/UX Designers  
- QA Engineers
- Backend Engineers (for API integration context)

## Integration with Project Architecture
This guide complements the system architecture described in [ARCHITECTURE.md](./ARCHITECTURE.md) and development practices in [DEVELOPMENT.md](./DEVELOPMENT.md).

---

## 1. Technology Stack

### Core Technologies (as per project specifications)
- **Framework**: React 18+ with Next.js 14
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS
- **Component Library**: Shadcn UI (built on Radix UI primitives)
- **Icons**: Lucide React
- **Map Visualization**: Leaflet
- **State Management**: React Context API
- **API Client**: Fetch API with custom hooks

### File Structure
```
web-app/src/
├── components/       # Reusable UI components
│   ├── map/         # Map-related components
│   ├── ui/          # Shadcn UI components
│   └── common/      # Shared components
├── hooks/           # Custom React hooks
├── utils/           # Helper functions
├── types/           # TypeScript type definitions
└── styles/          # Global styles and Tailwind config
```

---

## 2. Design Tokens

### Color System

#### Brand Colors
```css
--primary: #2563eb;        /* Blue 600 - Primary actions */
--primary-hover: #1d4ed8;  /* Blue 700 - Hover state */
--secondary: #64748b;      /* Slate 500 - Secondary elements */
--accent: #10b981;         /* Emerald 500 - Success/positive */
--danger: #FF0000;         /* Red - Errors/destructive */
--warning: #FFFF00;        /* Yellow - Warnings */
```

#### Network Element Status Colors (per MIGRATION_STATUS.md)
```typescript
// Status Code 1 (Poles) - Circle markers with 50% fill opacity
export const SC1_COLORS = {
  0: '#808080',   // Gray - Unknown/Undefined
  1: '#0000FF',   // Blue - Active/Existing
  2: '#00FF00',   // Green - Planned
  3: '#FFFF00',   // Yellow - Under Construction
  4: '#FF0000',   // Red - Faulty/Needs Attention
  5: '#800080'    // Purple - Decommissioned
}

// Status Code 3 (Connections/Junction Boxes) - Square markers with 50% fill opacity
export const SC3_COLORS = {
  0: '#808080',   // Gray - Unknown/Undefined
  1: '#0000FF',   // Blue - Active/Connected
  2: '#00FF00',   // Green - Planned
  3: '#FFFF00',   // Yellow - Under Construction
  4: '#FF0000',   // Red - Faulty/Needs Attention
  5: '#800080'    // Purple - Decommissioned
}

// Status Code 4 (Conductors/Cables) - Lines (no fill)
export const SC4_COLORS = {
  0: '#808080',   // Gray - Not Specified
  1: '#FFA500',   // Orange - Planned (dashed line)
  2: '#FFFF00',   // Yellow - Installation in Progress (dashed line)
  3: '#00FF00',   // Green - Installed (solid line)
  4: '#0000FF',   // Blue - Energized
  5: '#FF0000',   // Red - Faulty
  6: '#800080'    // Purple - Decommissioned
}

// Element Sizes
export const ELEMENT_SIZES = {
  pole: {
    radius: 6,        // Circle radius in pixels
    fillOpacity: 0.5  // 50% transparency
  },
  connection: {
    width: 8,         // Square width/height in pixels
    opacity: 0.5      // 50% transparency
  }
}
```

### Typography
```css
--font-sans: system-ui, -apple-system, sans-serif;
--font-mono: 'SF Mono', 'Monaco', monospace;

/* Font Sizes */
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */
```

### Spacing
Using Tailwind's spacing scale (multiples of 0.25rem):
- `space-1`: 0.25rem (4px)
- `space-2`: 0.5rem (8px)
- `space-4`: 1rem (16px)
- `space-6`: 1.5rem (24px)
- `space-8`: 2rem (32px)

### Breakpoints
```css
--screen-sm: 640px;   /* Mobile landscape */
--screen-md: 768px;   /* Tablet */
--screen-lg: 1024px;  /* Desktop */
--screen-xl: 1280px;  /* Large desktop */
--screen-2xl: 1536px; /* Extra large */
```

---

## 3. Component Patterns

### Layout Components

#### Main Application Layout
```tsx
<div className="h-screen flex flex-col">
  {/* Header */}
  <header className="h-16 border-b bg-white shadow-sm">
    {/* Navigation, user menu, site selector */}
  </header>
  
  {/* Main Content */}
  <main className="flex-1 flex overflow-hidden">
    {/* Sidebar */}
    <aside className="w-64 border-r bg-gray-50">
      {/* Tools, layers, filters */}
    </aside>
    
    {/* Map Container */}
    <div className="flex-1 relative">
      {/* Leaflet map */}
    </div>
    
    {/* Detail Panel */}
    <aside className="w-96 border-l bg-white">
      {/* Element details, edit forms */}
    </aside>
  </main>
</div>
```

### Form Components

#### Input Fields
```tsx
<div className="space-y-2">
  <Label htmlFor="field-id">Field Label</Label>
  <Input 
    id="field-id"
    type="text"
    placeholder="Enter value..."
    className="w-full"
  />
  <p className="text-sm text-gray-500">Helper text</p>
</div>
```

#### Select Dropdowns (using Shadcn)
```tsx
<Select value={value} onValueChange={setValue}>
  <SelectTrigger className="w-full">
    <SelectValue placeholder="Select option" />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="option1">Option 1</SelectItem>
    <SelectItem value="option2">Option 2</SelectItem>
  </SelectContent>
</Select>
```

### Button Hierarchy
```tsx
// Primary Action
<Button variant="default" size="default">
  Save Changes
</Button>

// Secondary Action
<Button variant="outline" size="default">
  Cancel
</Button>

// Destructive Action
<Button variant="destructive" size="default">
  Delete
</Button>

// Icon Button
<Button variant="ghost" size="icon">
  <Settings className="h-4 w-4" />
</Button>
```

### Data Display

#### Tables (Network Elements)
```tsx
<Table>
  <TableHeader>
    <TableRow>
      <TableHead>ID</TableHead>
      <TableHead>Name</TableHead>
      <TableHead>Type</TableHead>
      <TableHead>Status</TableHead>
      <TableHead className="text-right">Actions</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    {elements.map((element) => (
      <TableRow key={element.id}>
        <TableCell>{element.id}</TableCell>
        <TableCell>{element.name}</TableCell>
        <TableCell>{element.type}</TableCell>
        <TableCell>
          <Badge variant={getStatusVariant(element.status)}>
            {element.status}
          </Badge>
        </TableCell>
        <TableCell className="text-right">
          <Button variant="ghost" size="sm">Edit</Button>
        </TableCell>
      </TableRow>
    ))}
  </TableBody>
</Table>
```

### Map Components

#### Map Markers (per ClientMap.tsx)
```typescript
// Pole Markers
L.circleMarker([lat, lng], {
  radius: 3,
  fillColor: SC1_COLORS[status],
  color: '#000',
  weight: 1,
  opacity: 1,
  fillOpacity: 0.5,
  pane: 'polesPane'
})

// Connection Markers  
L.divIcon({
  html: `<div style="
    background-color: ${SC3_COLORS[status]}; 
    opacity: 0.5; 
    width: 8px; 
    height: 8px;
  "></div>`,
  className: 'connection-square-marker',
  iconSize: [8, 8]
})

// Conductor Lines
L.polyline(coordinates, {
  color: SC4_COLORS[status],
  weight: 2,
  opacity: 0.7,
  pane: 'conductorsPane',
  dashArray: status < 3 ? '5, 10' : undefined  // Dashed for planned/in-progress, solid for installed
})
```

---

## 4. Interaction Patterns

### Loading States
```tsx
// Full page loading
<div className="h-screen flex items-center justify-center">
  <div className="text-center">
    <Zap className="h-12 w-12 text-primary mx-auto mb-4 animate-pulse" />
    <h2 className="text-xl font-semibold">Loading Network Data...</h2>
    <Progress value={progress} className="w-64 mt-4" />
  </div>
</div>

// Inline loading
<Button disabled>
  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
  Processing...
</Button>
```

### Error Handling
```tsx
<Alert variant="destructive">
  <AlertCircle className="h-4 w-4" />
  <AlertTitle>Error</AlertTitle>
  <AlertDescription>
    {error.message}
  </AlertDescription>
</Alert>
```

### Toast Notifications
```tsx
toast({
  title: "Success",
  description: "Network element updated successfully",
  variant: "default", // or "destructive" for errors
})
```

---

## 5. Accessibility Guidelines

### WCAG 2.1 AA Compliance
- Minimum contrast ratio: 4.5:1 for normal text, 3:1 for large text
- All interactive elements must be keyboard accessible
- Focus indicators must be visible
- Form fields must have associated labels
- Error messages must be programmatically associated with inputs

### Keyboard Navigation
```tsx
// Tab order follows visual layout
// Escape key closes modals/dropdowns
// Enter/Space activates buttons
// Arrow keys navigate menus
```

### ARIA Attributes
```tsx
<button
  aria-label="Delete pole"
  aria-describedby="delete-warning"
  aria-pressed={isSelected}
>
  <Trash2 className="h-4 w-4" />
</button>
```

---

## 6. Performance Guidelines

### Map Rendering (per ClientMap.tsx optimizations)
- Batch render network elements in chunks of 20 (poles/connections) or 10 (conductors)
- Use requestAnimationFrame for smooth rendering
- Implement marker clustering for large datasets
- Defer non-critical rendering operations

### Image Optimization
- Use WebP format where supported
- Lazy load images below the fold
- Implement responsive images with srcset

### Code Splitting
```tsx
// Lazy load heavy components
const MapComponent = lazy(() => import('@/components/map/ClientMap'))
const ReportGenerator = lazy(() => import('@/components/reports/Generator'))
```

---

## 7. Testing Guidelines

### Component Testing
```tsx
// Example test for network element form
describe('NetworkElementForm', () => {
  it('validates required fields', async () => {
    render(<NetworkElementForm />)
    const submitButton = screen.getByRole('button', { name: /submit/i })
    fireEvent.click(submitButton)
    
    expect(await screen.findByText(/name is required/i)).toBeInTheDocument()
  })
})
```

### Visual Regression Testing
- Use Storybook for component documentation
- Implement visual regression tests for critical UI components
- Test responsive layouts at all breakpoints

---

## 8. Documentation Standards

### Component Documentation
```tsx
/**
 * NetworkElementCard - Displays summary information for a network element
 * 
 * @param {Object} props
 * @param {NetworkElement} props.element - The network element to display
 * @param {boolean} props.isSelected - Whether the element is selected
 * @param {Function} props.onSelect - Callback when element is selected
 * 
 * @example
 * <NetworkElementCard
 *   element={pole}
 *   isSelected={selectedId === pole.id}
 *   onSelect={(el) => setSelected(el)}
 * />
 */
```

### Storybook Stories
```tsx
export default {
  title: 'Components/NetworkElementCard',
  component: NetworkElementCard,
}

export const Default = {
  args: {
    element: mockPole,
    isSelected: false,
  },
}

export const Selected = {
  args: {
    element: mockPole,
    isSelected: true,
  },
}
```

---

## 9. Version Control & Updates

### Semantic Versioning
- MAJOR: Breaking changes to component APIs
- MINOR: New features, backwards compatible
- PATCH: Bug fixes, performance improvements

### Migration Guides
Document all breaking changes with migration examples in [MIGRATION_STATUS.md](../MIGRATION_STATUS.md)

---

## References

- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture overview
- [DEVELOPMENT.md](./DEVELOPMENT.md) - Development setup and practices
- [API.md](./API.md) - Backend API documentation
- [MIGRATION_STATUS.md](../MIGRATION_STATUS.md) - Migration progress and network data structure
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Shadcn UI Components](https://ui.shadcn.com)
- [Leaflet Documentation](https://leafletjs.com)

---

*Last Updated: August 2024*
*Version: 1.0.0*
