import requests
import json
from pathlib import Path

def test_pattern_svg_api():
    """Test the SVG API with dress_pencil_specification.json (same input as 3D endpoint)"""
    
    # Load the pattern specification
    pattern_file = Path("./assets/Patterns/hoody_mean_specification.json")
    if not pattern_file.exists():
        print(f"Error: Pattern file not found at {pattern_file}")
        print("Make sure hoody_mean_specification.json exists in assets/Patterns/")
        return
    
    with open(pattern_file, 'r') as f:
        pattern_specification = json.load(f)
    
    # Prepare the request (SAME FORMAT AS 3D ENDPOINT)
    test_data = {
        "pattern_specification": pattern_specification,
        "body_params": None  # Use default body
    }
    
    # API endpoint for SVG generation
    url = "http://localhost:8000/generate_svg"
    
    print("🎨 Sending pattern specification to SVG API...")
    print(f"📋 Pattern has {len(pattern_specification['pattern']['panels'])} panels")
    
    try:
        # Send request
        response = requests.post(url, json=test_data, timeout=300)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"📁 Session ID: {result['session_id']}")
            print(f"🖼️ SVG file: {result['svg_file_path']}")
            print(f"📸 PNG file: {result['png_file_path']}")
            print(f" Output directory: {result['output_dir']}")
            
            # Download the generated files
            session_id = result['session_id']
            
            # Download SVG
            svg_download_url = f"http://localhost:8000/download_svg/{session_id}"
            print(f"\n📥 Downloading SVG from: {svg_download_url}")
            
            svg_response = requests.get(svg_download_url)
            if svg_response.status_code == 200:
                svg_filename = f"dress_pattern_{session_id}.svg"
                with open(svg_filename, 'wb') as f:
                    f.write(svg_response.content)
                print(f"💾 SVG saved as: {svg_filename}")
            else:
                print(f"❌ Failed to download SVG: {svg_response.status_code}")
            
            # Download PNG
            png_download_url = f"http://localhost:8000/download_png/{session_id}"
            print(f"📥 Downloading PNG from: {png_download_url}")
            
            png_response = requests.get(png_download_url)
            if png_response.status_code == 200:
                png_filename = f"dress_pattern_{session_id}.png"
                with open(png_filename, 'wb') as f:
                    f.write(png_response.content)
                print(f"💾 PNG saved as: {png_filename}")
            else:
                print(f"❌ Failed to download PNG: {png_response.status_code}")
            
            print(f"\n🎉 SVG and PNG files downloaded successfully!")
            print(f"🧹 You can clean up the session with: DELETE /cleanup_svg/{session_id}")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"🔌 Connection error: {e}")
        print("Make sure the API server is running with: python api_garment_3d_service.py")
    except Exception as e:
        print(f"💥 Unexpected error: {e}")

if __name__ == "__main__":
    print("🎯 Testing SVG Pattern Generation API")
    print("=" * 60)
    
    # Test with dress pattern
    test_pattern_svg_api()

    
    print("\n" + "="*60)
    print("✨ Testing complete! Check the generated files.")
