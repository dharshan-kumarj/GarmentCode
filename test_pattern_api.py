import requests
import json
from pathlib import Path

def test_pattern_specification_api():
    """Test the API with dress_pencil_specification.json"""
    
    # Load the pattern specification
    pattern_file = Path("./assets/Patterns/patterns.json")
    with open(pattern_file, 'r') as f:
        pattern_specification = json.load(f)
    
    # Prepare the request
    test_data = {
        "pattern_specification": pattern_specification,
        "body_params": None  # Use default body
    }
    
    # API endpoint
    url = "http://localhost:8000/generate3d"
    
    print("Sending pattern specification to API...")
    print(f"Pattern has {len(pattern_specification['pattern']['panels'])} panels")
    
    try:
        # Send request
        response = requests.post(url, json=test_data, timeout=300)
        
        if response.status_code == 200:
            result = response.json()
            print("Success!")
            print(f"Session ID: {result['session_id']}")
            print(f"GLB file: {result['glb_file_path']}")
            print(f"Output directory: {result['output_dir']}")
            
            # You can now download the GLB file
            download_url = f"http://localhost:8000/download/{result['session_id']}"
            print(f"Download URL: {download_url}")
            
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")
        print("Make sure the API server is running with: python api_garment_3d_service.py")

if __name__ == "__main__":
    test_pattern_specification_api()
