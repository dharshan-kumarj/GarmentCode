# Garment 3D Generation Service API

A RESTful API service for generating 3D garment files from pattern parameters using FastAPI.

## Base URL
```
http://localhost:8000
```

## Testing the API

### Quick Test with test_api.py

A test script is provided to quickly verify the API is working correctly:

```bash
# Make sure the API service is running first
python api_garment_3d_service.py

# In another terminal, run the test
python test_api.py
```

The test script will:
1. Send a POST request to `/generate3d` with sample garment parameters
2. Display the response including session ID and file paths
3. Show any errors if the request fails

**Expected successful response:**
```json
{
  "session_id": "uuid-string",
  "glb_file_path": "/path/to/generated/file.glb", 
  "output_dir": "/path/to/output/directory"
}
```

### Full Test Workflow

For a complete test including file download:

```python
import requests
import json

# 1. Generate 3D garment (using data from test_api.py)
response = requests.post("http://localhost:8000/generate3d", json=test_data)
if response.ok:
    result = response.json()
    session_id = result["session_id"]
    
    # 2. Download the GLB file
    download_response = requests.get(f"http://localhost:8000/download/{session_id}")
    if download_response.ok:
        with open(f"garment_{session_id}.glb", "wb") as f:
            f.write(download_response.content)
        print("GLB file downloaded successfully")
    
    # 3. Cleanup when done
    cleanup_response = requests.delete(f"http://localhost:8000/cleanup/{session_id}")
    print("Session cleaned up")
```

## Endpoints

### 1. Generate 3D Garment
Generate 3D files from garment design parameters.

**Endpoint:** `POST /generate3d`

**Request Body:**
```json
{
  "design_params": {
    "meta": { ... },
    "shirt": { ... },
    "sleeve": { ... },
    "collar": { ... },
    "left": { ... }
  },
  "body_params": { ... } // Optional
}
```

**Response:**
```json
{
  "session_id": "uuid-string",
  "glb_file_path": "/path/to/generated/file.glb",
  "output_dir": "/path/to/output/directory"
}
```

**Status Codes:**
- `200 OK` - Successful generation
- `500 Internal Server Error` - Generation failed

### 2. Download GLB File
Download the generated 3D GLB file.

**Endpoint:** `GET /download/{session_id}`

**Parameters:**
- `session_id` (path) - Session ID returned from generate3d

**Response:**
- Binary GLB file with `Content-Type: model/gltf-binary`

**Status Codes:**
- `200 OK` - File found and returned
- `404 Not Found` - GLB file not found for session
- `500 Internal Server Error` - Download failed

### 3. Cleanup Session
Clean up temporary files for a session.

**Endpoint:** `DELETE /cleanup/{session_id}`

**Parameters:**
- `session_id` (path) - Session ID to clean up

**Response:**
```json
{
  "status": "success",
  "message": "Session {session_id} cleaned up"
}
```

**Status Codes:**
- `200 OK` - Cleanup successful
- `500 Internal Server Error` - Cleanup failed

## Design Parameters Structure

### Meta Parameters
Controls which garment components to include:
```json
"meta": {
  "upper": {
    "v": "FittedShirt",
    "type": "select_null",
    "range": ["FittedShirt", "Shirt", null],
    "default_prob": 0.3
  },
  "bottom": {
    "v": null,
    "type": "select_null", 
    "range": ["SkirtCircle", "AsymmSkirtCircle", "GodetSkirt", "Pants", "Skirt2", "SkirtManyPanels", "PencilSkirt", "SkirtLevels", null],
    "default_prob": 0.3
  },
  "wb": {
    "v": null,
    "type": "select_null",
    "range": ["StraightWB", "FittedWB", null],
    "default_prob": 0.5
  }
}
```

### Shirt Parameters
Controls shirt/top characteristics:
```json
"shirt": {
  "width": {"v": 1.05, "type": "float", "range": [1.0, 1.3], "default_prob": 0.4},
  "strapless": {"v": false, "type": "bool", "range": [true, false], "default_prob": 0.8},
  "length": {"v": 1.2, "type": "float", "range": [0.5, 3.5], "default_prob": 0.7},
  "flare": {"v": 1.0, "type": "float", "range": [0.7, 1.6], "default_prob": 0.4}
}
```

### Sleeve Parameters
Controls sleeve design:
```json
"sleeve": {
  "sleeveless": {"v": true, "type": "bool", "range": [true, false], "default_prob": 0.7},
  "armhole_shape": {"v": "ArmholeCurve", "type": "select", "range": ["ArmholeSquare", "ArmholeAngle", "ArmholeCurve"], "default_prob": 0.7},
  "length": {"v": 0.3, "type": "float", "range": [0.1, 1.15]},
  "connecting_width": {"v": 0.2, "type": "float", "range": [0, 2], "default_prob": 0.6},
  "end_width": {"v": 1.0, "type": "float", "range": [0.2, 2], "default_prob": 0.4},
  "sleeve_angle": {"v": 10, "type": "int", "range": [10, 50]},
  "smoothing_coeff": {"v": 0.25, "type": "float", "range": [0.1, 0.4], "default_prob": 0.8},
  "opening_dir_mix": {"v": 0.1, "type": "float", "range": [-0.9, 0.8], "default_prob": 1.0},
  "standing_shoulder": {"v": false, "type": "bool", "range": [true, false], "default_prob": 0.8},
  "standing_shoulder_len": {"v": 5.0, "type": "float", "range": [4, 10]},
  "connect_ruffle": {"v": 1, "type": "float", "range": [1, 2], "default_prob": 0.4},
  "cuff": {
    "type": {"v": null, "type": "select_null", "range": ["CuffBand", "CuffSkirt", "CuffBandSkirt", null]},
    "cuff_len": {"v": 0.1, "type": "float", "range": [0.05, 0.9], "default_prob": 0.7},
    "skirt_flare": {"v": 1.2, "type": "float", "range": [1, 2]},
    "skirt_fraction": {"v": 0.5, "type": "float", "range": [0.1, 0.9], "default_prob": 0.5},
    "skirt_ruffle": {"v": 1.0, "type": "float", "range": [1, 1.5], "default_prob": 0.3},
    "top_ruffle": {"v": 1, "type": "float", "range": [1, 3]}
  }
}
```

### Collar Parameters
Controls neckline and collar design:
```json
"collar": {
  "f_collar": {"v": "CircleNeckHalf", "type": "select", "range": ["CircleNeckHalf", "CurvyNeckHalf", "VNeckHalf", "SquareNeckHalf", "TrapezoidNeckHalf", "CircleArcNeckHalf", "Bezier2NeckHalf"], "default_prob": 0.4},
  "b_collar": {"v": "CircleNeckHalf", "type": "select", "range": ["CircleNeckHalf", "CurvyNeckHalf", "VNeckHalf", "SquareNeckHalf", "TrapezoidNeckHalf", "CircleArcNeckHalf", "Bezier2NeckHalf"], "default_prob": 0.8},
  "width": {"v": 0.2, "type": "float", "range": [-0.5, 1], "default_prob": 0.4},
  "fc_depth": {"v": 0.4, "type": "float", "range": [0.3, 2], "default_prob": 0.3},
  "bc_depth": {"v": 0, "type": "float", "range": [0, 2], "default_prob": 0.4},
  "fc_angle": {"v": 95, "type": "int", "range": [70, 110]},
  "bc_angle": {"v": 95, "type": "int", "range": [70, 110]},
  "component": {
    "style": {"v": null, "type": "select_null", "range": ["Turtle", "SimpleLapel", "Hood2Panels", null], "default_prob": 0.6},
    "depth": {"v": 7, "type": "int", "range": [2, 8]},
    "lapel_standing": {"v": false, "type": "bool", "range": [true, false]},
    "hood_depth": {"v": 1, "type": "float", "range": [1, 2], "default_prob": 0.6},
    "hood_length": {"v": 1, "type": "float", "range": [1, 1.5], "default_prob": 0.6}
  }
}
```

### Left Side Parameters (for asymmetric designs)
```json
"left": {
  "enable_asym": {"v": false, "type": "bool", "range": [true, false], "default_prob": 0.8},
  "shirt": { /* Similar to main shirt params */ },
  "sleeve": { /* Similar to main sleeve params */ },
  "collar": { /* Similar to main collar params */ }
}
```

## Usage Examples

### Python Example
```python
import requests
import json

# Prepare request data
data = {
    "design_params": {
        "meta": {
            "upper": {"v": "FittedShirt", "type": "select_null", "range": ["FittedShirt", "Shirt", None], "default_prob": 0.3},
            "bottom": {"v": None, "type": "select_null", "range": ["SkirtCircle", "Pants", None], "default_prob": 0.3}
        },
        "shirt": {
            "width": {"v": 1.05, "type": "float", "range": [1.0, 1.3], "default_prob": 0.4},
            "length": {"v": 1.2, "type": "float", "range": [0.5, 3.5], "default_prob": 0.7}
        }
        # ... other parameters
    }
}

# Generate 3D garment
response = requests.post("http://localhost:8000/generate3d", json=data)
if response.ok:
    result = response.json()
    session_id = result["session_id"]
    print(f"Generated successfully. Session ID: {session_id}")
    
    # Download the GLB file
    download_response = requests.get(f"http://localhost:8000/download/{session_id}")
    if download_response.ok:
        with open("garment.glb", "wb") as f:
            f.write(download_response.content)
        print("GLB file downloaded successfully")
    
    # Cleanup when done
    cleanup_response = requests.delete(f"http://localhost:8000/cleanup/{session_id}")
    print("Session cleaned up")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

### cURL Example
```bash
# Generate 3D garment
curl -X POST "http://localhost:8000/generate3d" \
     -H "Content-Type: application/json" \
     -d @request_data.json

# Download GLB file
curl -X GET "http://localhost:8000/download/{session_id}" \
     -o garment.glb

# Cleanup session
curl -X DELETE "http://localhost:8000/cleanup/{session_id}"
```

## Parameter Types

- `float`: Floating-point number within specified range
- `int`: Integer within specified range  
- `bool`: Boolean true/false
- `select`: Must be one of the values in range array
- `select_null`: Can be one of the values in range array or null

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200 OK`: Success
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error with detailed message

Error responses include detailed error messages and stack traces for debugging.

## Running the Service

```bash
# Start the service
python api_garment_3d_service.py

# Or with uvicorn directly
uvicorn api_garment_3d_service:app --host 0.0.0.0 --port 8000 --log-level debug
```

The service will be available at `http://localhost:8000` with automatic API documentation at `http://localhost:8000/docs`.
