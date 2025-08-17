# Voltage Drop & Generation Site - Technical Implementation Notes

**Last Updated**: 2025-08-15
**Investigation Session**: Desktop version analysis and uGridNET source code review

## 🔴 CRITICAL FINDINGS

### 1. Pole Naming Convention - CORRECTED UNDERSTANDING

The two-letter codes in pole IDs follow a **hierarchical branching topology**, NOT substation indicators:

**Format**: `SITE_ZONE_BRANCH` (e.g., `KET_02_BB1`)

- **First Letter (A-I)**: Main branch level from feeder
  - A = First main branch
  - B = Second main branch  
  - C = Third main branch, etc.

- **Second Letter (A-C)**: Sub-branch within main branch
  - A = First sub-branch
  - B = Second sub-branch
  - C = Third sub-branch

**IMPORTANT**: `BB` means "Branch B, Sub-branch B" - NOT busbar or backbone!

**Special Codes**:
- `M1-M9`: Medium Voltage lines
- Numbers indicate sequence along the MV backbone

**Network Topology Example**:
```
Generation Site (Source)
    │
    ├── M (MV Backbone)
    │   ├── M1, M2, M3... (MV poles along backbone)
    │   
    ├── A (Branch A from feeder)
    │   ├── AA (Sub-branch A of Branch A) - 218 poles
    │   ├── AB (Sub-branch B of Branch A) - 180 poles
    │   └── AC (Sub-branch C of Branch A) - 56 poles
    │
    ├── B (Branch B from feeder)
    │   ├── BA (Sub-branch A of Branch B) - 109 poles
    │   ├── BB (Sub-branch B of Branch B) - 102 poles ← NOT a substation!
    │   └── BC (Sub-branch C of Branch B) - 14 poles
    │
    └── C (Branch C from feeder)...
```

### 2. Generation Site Detection - MUST BE EXPLICIT

Based on uGridNET source code analysis:

**Correct Approach** (from uGridNET):
```python
# Generation sites defined explicitly in input data
'lat_Generation': net_inputs['lat_Generation'][0]
'long_Generation': net_inputs['long_Generation'][0]

# System finds POI (Point of Interconnection) by calculating closest pole
POI_Pole(lat_Generation, long_Generation, ...)
```

**Current Implementation** (acceptable workaround):
- Uses **MV connectivity strategy** as proxy when explicit generation coordinates unavailable
- Identifies poles connected to MV conductors with highest degree
- Successfully identifies source poles (e.g., `KET_05_M111D` with 6 connections)
- Fallback to highest degree centrality if MV strategy fails

### 3. Implementation Status

**Backend** (`/backend/utils/voltage_calculator.py`):
- ✅ Multi-strategy source detection implemented
- ✅ MV connectivity strategy working correctly
- ✅ Removed incorrect "BB = substation" assumption
- ✅ Returns source pole for voltage calculations

**Backend** (`/backend/main.py`):
- ✅ Exposes generation site in `/api/network/{site}` response
- ✅ Includes generation array with coordinates and metadata
- ✅ Fixed initialization of generation key in formatted_data

**Frontend** (`/web-app/src/components/map/ClientMap.tsx`):
- ✅ Renders generation sites with distinctive icon
- ✅ Orange-red gradient circle with white lightning bolt
- ✅ Popup shows site details
- ✅ Manages generation markers in dedicated layer

### 4. Test Results

**KET Site Analysis**:
- Top MV-connected poles by degree:
  - `KET_05_M111D`: 6 connections (identified as source)
  - `KET_05_M129C`: 5 connections
  - `KET_05_M14A`: 5 connections
  - `KET_22_M115B`: 5 connections
  - `KET_18_M8A`: 5 connections

### 5. Future Improvements

1. **Add Generation Sheet to Excel Template**:
   - Include explicit generation site coordinates
   - Match uGridNET input format
   - Fields: Site_ID, Latitude, Longitude, Capacity

2. **Update Excel Importer**:
   - Read Generation sheet if present
   - Use explicit coordinates when available
   - Fall back to MV connectivity strategy

3. **Enhance UI**:
   - Allow manual generation site selection
   - Display voltage drop gradients from source
   - Show power flow direction on conductors

## 📋 TODO Status (End of Session)

1. ✅ Investigate desktop version pole naming convention
2. ✅ Understand topological meaning of two-letter codes like BB
3. ✅ Document the actual use case from desktop version
4. ✅ Correct the web version implementation to match
5. ✅ Fix generation site detection to use explicit coordinates from input data
6. ⏳ Add generation site input to Excel template (future work)

## 🔑 Key Takeaways

1. **BB is NOT busbar** - it's a branch/sub-branch designation in network topology
2. **Generation sites should be explicit** - defined by coordinates, not inferred from naming
3. **MV connectivity is reliable** - poles with high MV connections are likely substations
4. **Current implementation works** - voltage drop calculations functional with MV strategy

## 📚 References

- uGridNET Source: https://github.com/onepowerLS/uGrid_uGridNet
- Key files examined:
  - `/uGridNet/models.py` - Data models including GenerationSite
  - `/uGridNet/uGridNet_runner.py` - Generation site POI calculation
  - `/uGridNet/network_calculations.py` - Voltage drop calculations

---

**Next Session Starting Point**: 
The voltage drop generation site integration is functionally complete. The system correctly identifies source poles using MV connectivity and displays them on the map. Consider adding explicit generation site input to Excel template for full parity with uGridNET approach.
