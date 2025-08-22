# Map Layer Fixes - Implementation Plan

## Issue Identified
**Date:** 2024-08-22  
**Problem:** Pole markers are not correctly assigned to voltage-specific panes

### Current State
- All poles are assigned to a generic `'polesPane'` that doesn't exist
- The created `lvPolesPane` (z-index: 500) and `mvPolesPane` (z-index: 550) are unused
- No differentiation between LV and MV poles in the rendering logic

### Expected Behavior
Based on the layering specification:
1. **LV Poles** should use `lvPolesPane` (z-index: 500)
2. **MV Poles** should use `mvPolesPane` (z-index: 550) - rendered above LV poles
3. This matches the conductor implementation which correctly differentiates between voltage levels

## Implementation Plan

### Step 1: Determine Pole Voltage Level
- Check if pole data contains voltage level indicator (e.g., `voltage_level`, `type`, or similar field)
- If not available, may need to infer from connected conductors or add a default

### Step 2: Update Pole Rendering Logic
```typescript
// Determine pane based on voltage level
let polePane = 'lvPolesPane';  // Default to LV
if (pole.voltage_level === 'MV' || pole.type === 'MV') {
  polePane = 'mvPolesPane';
}

const circleMarker = L.circleMarker([pole.lat, pole.lng], {
  radius: 3,
  fillColor: color,
  color: '#000',
  weight: 1,
  opacity: 1,
  fillOpacity: 0.5,
  pane: polePane  // Use voltage-specific pane
})
```

### Step 3: Verify Layer Groups
Ensure layer groups reference the correct panes:
- `mvPoles` → `mvPolesPane`
- `lvPoles` → `lvPolesPane`

## Testing Plan
1. Load network data with both LV and MV poles
2. Verify MV poles render above LV poles
3. Check z-index ordering via browser dev tools
4. Test with KET network dataset which contains both voltage levels

## Additional Documentation Updates
- Updated UI_STYLE_GUIDE.md to reflect dashed lines for pre-installation conductors (status < 3)
- Documented layer ordering from bottom to top:
  1. Connections (400)
  2. LV Poles (500)
  3. MV Poles (550)
  4. Drop Lines (600)
  5. LV Lines (650)
  6. MV Lines (700)
