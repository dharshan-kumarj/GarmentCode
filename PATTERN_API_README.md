# Pattern Specification API

This API now supports direct pattern specification input for 3D garment generation.

## New Endpoint: `/generate3d`

Use this endpoint to generate 3D garments directly from pattern specification JSON files (like `dress_pencil_specification.json`).

### Request Format

```json
{
  "pattern_specification": {
    "pattern": {
      "panels": { ... },
      "stitches": [ ... ],
      "panel_order": [ ... ]
    },
    "parameters": {},
    "parameter_order": [],
    "properties": { ... }
  },
  "body_params": null  // Optional, uses default body if not provided
}
```

### Python Example

```python
import requests
import json

# Load pattern specification
with open('./assets/Patterns/dress_pencil_specification.json', 'r') as f:
    pattern_spec = json.load(f)

# Send request
response = requests.post(
    "http://localhost:8000/generate3d",
    json={
        "pattern_specification": pattern_spec,
        "body_params": None
    }
)

if response.status_code == 200:
    result = response.json()
    print(f"GLB file: {result['glb_file_path']}")
    print(f"Download URL: http://localhost:8000/download/{result['session_id']}")
```

## Legacy Endpoint: `/generate3d_legacy`

For backward compatibility, the old design_params endpoint is still available.

### Request Format

```json
{
  "design_params": {
    "meta": { ... },
    "shirt": { ... },
    "sleeve": { ... },
    "collar": { ... }
  },
  "body_params": null
}
```

## Running the API

```bash
python api_garment_3d_service.py
```

## Testing

```bash
# Test the new pattern specification endpoint
python test_pattern_api.py

# Test the legacy design params endpoint
python test_api.py
```

## Key Differences

1. **New endpoint (`/generate3d`)**: Accepts complete pattern specification JSON directly
   - No need to generate patterns from design parameters
   - Works directly with pre-defined pattern files
   - Faster processing since pattern generation is skipped

2. **Legacy endpoint (`/generate3d_legacy`)**: Uses design parameters to generate patterns first
   - Generates patterns using MetaGarment class
   - More flexible but slower processing
   - Maintained for backward compatibility

## Pattern Specification Format

The pattern specification should follow the standard GarmentCode JSON format with:
- `pattern.panels`: Panel definitions with vertices, edges, translations, rotations
- `pattern.stitches`: Stitch connections between panels
- `pattern.panel_order`: Order of panels for processing
- `properties`: Pattern properties and units
- `parameters`: Optional parametrization (can be empty)

Example files can be found in `./assets/Patterns/` directory.
