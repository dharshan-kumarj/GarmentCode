from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
from pathlib import Path
import logging
import traceback
import sys

from pattern_data_sim import GarmentTo3DService

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Pydantic models for request/response
class Generate3DRequest(BaseModel):
    design_params: Dict[str, Any]
    body_params: Optional[Dict[str, Any]] = None

class Generate3DResponse(BaseModel):
    session_id: str
    glb_file_path: str
    output_dir: str

# Initialize FastAPI app
app = FastAPI(
    title="Garment 3D Generation Service",
    description="Service for generating 3D garment files from patterns",
    version="1.0.0"
)

# Initialize the 3D generation service
try:
    service = GarmentTo3DService(output_root="./tmp_3d_service")
    logger.info("3D Generation Service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize 3D Generation Service: {str(e)}")
    logger.error(traceback.format_exc())
    raise

@app.post("/generate3d", response_model=Generate3DResponse)
async def generate_3d(request: Generate3DRequest):
    """Generate 3D files from garment parameters
    
    Args:
        request: Generate3DRequest containing design and optional body parameters
        
    Returns:
        Generate3DResponse with session ID and file paths
    """
    try:
        logger.info("Received generate3d request")
        logger.debug(f"Design params: {request.design_params}")
        if request.body_params:
            logger.debug(f"Body params: {request.body_params}")

        # Generate unique session ID
        session_id = str(uuid.uuid4())
        logger.info(f"Created session ID: {session_id}")
        
        # Generate 3D files
        logger.info("Starting 3D generation")
        output_dir, glb_path = service.generate_3d(
            design_params=request.design_params,
            session_id=session_id,
            body_params=request.body_params
        )
        logger.info(f"3D generation completed. Output dir: {output_dir}, GLB path: {glb_path}")
        
        return Generate3DResponse(
            session_id=session_id,
            glb_file_path=str(glb_path),
            output_dir=str(output_dir)
        )
    except Exception as e:
        logger.error(f"Error in generate_3d: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error in 3D generation: {str(e)}\n{traceback.format_exc()}")

@app.get("/download/{session_id}")
async def download_glb(session_id: str):
    """Download the generated GLB file
    
    Args:
        session_id: Session ID from generate_3d request
        
    Returns:
        GLB file as attachment
    """
    try:
        logger.info(f"Received download request for session: {session_id}")
        # Find the GLB file in the session directory
        session_dir = Path("./tmp_3d_service") / session_id
        glb_files = list(session_dir.rglob("*.glb"))
        
        if not glb_files:
            logger.error(f"No GLB file found in session {session_id}")
            raise HTTPException(status_code=404, detail="GLB file not found")
            
        logger.info(f"Returning GLB file: {glb_files[0]}")
        return FileResponse(
            path=str(glb_files[0]),
            filename=glb_files[0].name,
            media_type="model/gltf-binary"
        )
    except Exception as e:
        logger.error(f"Error in download_glb: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/cleanup/{session_id}")
async def cleanup_session(session_id: str):
    """Clean up session files
    
    Args:
        session_id: Session to clean up
    """
    try:
        logger.info(f"Cleaning up session: {session_id}")
        service.cleanup_session(session_id)
        logger.info(f"Successfully cleaned up session: {session_id}")
        return {"status": "success", "message": f"Session {session_id} cleaned up"}
    except Exception as e:
        logger.error(f"Error in cleanup_session: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug") 