# SVG Pattern Generation Endpoint

## Overview

The new `/generate_pattern_svg` endpoint works exactly like the `/generate3d` endpoint but produces SVG pattern files instead of 3D models. This allows you to generate 2D pattern files directly from the same JSON input format.

## Endpoint Details

### Generate Pattern SVG
**Endpoint:** `POST /generate_pattern_svg`

**Input:** Same format as `/generate3d` endpoint
```json
{
  "pattern_specification": {
    "pattern": {
      "panels": { ... },
      "stitches": [ ... ],
      "panel_order": [ ... ]
    },
    "parameters": { ... },
    "parameter_order": [ ... ],
    "properties": { ... }
  },
  "body_params": null
}
```

**Output:**
```json
{
  "session_id": "uuid-string",
  "svg_file_path": "/path/to/pattern.svg",
  "png_file_path": "/path/to/pattern.png", 
  "printable_pdf_path": "/path/to/pattern.pdf",
  "output_dir": "/path/to/output/directory"
}
```

### Download Files

- **SVG:** `GET /download_svg/{session_id}`
- **PNG:** `GET /download_png/{session_id}`
- **PDF:** `GET /download_pdf/{session_id}`

### Cleanup

- **Cleanup:** `DELETE /cleanup_svg/{session_id}`

## Testing

### Test with dress_pencil_specification.json
```bash
python test_pattern_svg_api.py
```

### Compare 3D vs SVG endpoints
```bash
python compare_endpoints.py
```

### Web Interface
Open `svg_demo.html` in your browser and select "Use Direct Pattern JSON"

## Example Usage

```python
import requests
import json

# Load pattern specification
with open("assets/Patterns/dress_pencil_specification.json", 'r') as f:
    pattern_spec = json.load(f)

# Generate SVG
response = requests.post("http://localhost:8000/generate_pattern_svg", json={
    "pattern_specification": pattern_spec,
    "body_params": None
})

if response.status_code == 200:
    result = response.json()
    session_id = result["session_id"]
    
    # Download SVG
    svg_response = requests.get(f"http://localhost:8000/download_svg/{session_id}")
    with open("pattern.svg", "wb") as f:
        f.write(svg_response.content)
    
    print("SVG pattern generated successfully!")
```

## Key Features

1. **Same Input Format:** Uses identical JSON input as the 3D endpoint
2. **Multiple Output Formats:** Generates SVG, PNG, and PDF files
3. **Consistent API:** Same session management and download patterns
4. **Text Labels:** Includes panel names and annotations
5. **Printable PDF:** Optimized for physical printing and cutting

## Comparison: 3D vs SVG Endpoints

| Feature | generate3d | generate_pattern_svg |
|---------|------------|---------------------|
| Input Format | ✅ Same JSON | ✅ Same JSON |
| Output | GLB file (3D) | SVG/PNG/PDF (2D) |
| Session Management | ✅ | ✅ |
| Body Parameters | ✅ | ✅ |
| Cleanup | ✅ | ✅ |
| Use Case | 3D visualization | Pattern cutting |

Use `generate_pattern_svg` when you only need 2D pattern files without the computational overhead of 3D simulation.
