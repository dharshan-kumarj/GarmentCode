from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
from pathlib import Path
import logging
import traceback
import sys
import yaml
import json

from pattern_data_sim import GarmentTo3DService
# Custom imports for SVG generation
from assets.garment_programs.meta_garment import MetaGarment
from assets.bodies.body_params import BodyParameters

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
    pattern_specification: Dict[str, Any]  # JSON pattern specification like dress_pencil_specification.json
    body_params: Optional[Dict[str, Any]] = None

class Generate3DResponse(BaseModel):
    session_id: str
    glb_file_path: str
    output_dir: str

# Legacy request model for backward compatibility
class LegacyGenerate3DRequest(BaseModel):
    design_params: Dict[str, Any]
    body_params: Optional[Dict[str, Any]] = None

# New SVG generation models
class GenerateSVGRequest(BaseModel):
    pattern_specification: Dict[str, Any] = None
    design_params: Dict[str, Any] = None
    body_params: Optional[Dict[str, Any]] = None
    with_text: bool = True
    view_ids: bool = True
    with_printable: bool = False

class GenerateSVGResponse(BaseModel):
    session_id: str
    svg_file_path: str
    png_file_path: str
    output_dir: str
    printable_pdf_path: Optional[str] = None

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

class GarmentSVGService:
    """Service for generating SVG pattern files from JSON specifications"""
    
    def __init__(self, output_root: str = './tmp_svg_service'):
        """Initialize the SVG generation service
        
        Args:
            output_root: Root directory for output files
        """
        self.output_root = Path(output_root)
        self.output_root.mkdir(parents=True, exist_ok=True)
        
        # Load default body parameters
        self.default_body_params = BodyParameters(Path.cwd() / 'assets/bodies/mean_all.yaml')
    
    def generate_svg(self, 
                    design_params: Dict[str, Any] = None,
                    pattern_specification: Dict[str, Any] = None,
                    session_id: str = None,
                    body_params: Optional[Dict[str, Any]] = None,
                    with_text: bool = True,
                    view_ids: bool = True,
                    with_printable: bool = False) -> tuple[Path, Path, Path, Path]:
        """Generate SVG pattern files from garment parameters OR pattern specification
        
        Args:
            design_params: Dictionary of design parameters
            pattern_specification: Direct pattern specification JSON  
            session_id: Unique session identifier
            body_params: Optional custom body parameters
            with_text: Include panel names in SVG
            view_ids: Include vertex/edge IDs in SVG
            with_printable: Generate printable PDF version
            
        Returns:
            Tuple of (output directory, SVG file path, PNG file path, PDF file path or None)
        """
        if design_params is None and pattern_specification is None:
            raise ValueError("Either design_params or pattern_specification must be provided")
        
        # Create session directory
        session_dir = self.output_root / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        # Setup body parameters
        if body_params:
            body = BodyParameters()
            body.load_from_dict(body_params)
        else:
            body = self.default_body_params

        if pattern_specification is not None:
            # Use pattern specification directly - create a MetaGarment from it
            # For pattern specifications, we need to convert them to design_params format
            # This is a simplified approach - you might need to adapt based on your pattern format
            pattern_name = "user_pattern_svg"
            return self._generate_svg_from_pattern_spec(pattern_specification, session_dir, body, 
                                                      pattern_name, with_text, view_ids, with_printable)
        else:
            # Use design parameters to generate pattern
            return self._generate_svg_from_design_params(design_params, session_dir, body,
                                                        with_text, view_ids, with_printable)

    def _generate_svg_from_design_params(self, design_params: Dict[str, Any], 
                                       session_dir: Path, body: BodyParameters,
                                       with_text: bool, view_ids: bool, with_printable: bool) -> tuple[Path, Path, Path, Path]:
        """Generate SVG from design parameters"""
        try:
            # Create garment pattern using MetaGarment
            sew_pattern = MetaGarment('SVG_Pattern', body, design_params)
            
            # Get the pattern assembly
            pattern = sew_pattern.assembly()
            
            # Serialize to generate SVG files
            pattern_folder = pattern.serialize(
                session_dir,
                to_subfolder=True,
                with_3d=False,  # Skip 3D generation
                with_text=with_text,
                view_ids=view_ids,
                with_printable=with_printable,
                empty_ok=True
            )
            pattern_folder = Path(pattern_folder)
            
            # Save parameters for reference
            body.save(pattern_folder)
            with open(pattern_folder / 'design_params.yaml', 'w') as f:
                yaml.dump({'design': design_params}, f, default_flow_style=False, sort_keys=False)
            
            # Find generated files
            svg_file = pattern_folder / f'{sew_pattern.name}_pattern.svg'
            png_file = pattern_folder / f'{sew_pattern.name}_pattern.png'
            pdf_file = pattern_folder / f'{sew_pattern.name}_print_pattern.pdf' if with_printable else None
            
            return pattern_folder, svg_file, png_file, pdf_file
            
        except Exception as e:
            logger.error(f"Error generating SVG from design params: {str(e)}")
            raise

    def _generate_svg_from_pattern_spec(self, pattern_specification: Dict[str, Any], 
                                      session_dir: Path, body: BodyParameters, pattern_name: str,
                                      with_text: bool, view_ids: bool, with_printable: bool) -> tuple[Path, Path, Path, Path]:
        """Generate SVG from pattern specification JSON - Direct pattern loading like 3D endpoint"""
        try:
            # Save pattern specification to file in the correct format expected by VisPattern
            pattern_file = session_dir / f"{pattern_name}_specification.json"
            
            with open(pattern_file, 'w') as f:
                json.dump(pattern_specification, f, indent=2)
            
            # Load pattern directly using VisPattern (pass the file path to constructor)
            from pygarment.pattern.wrappers import VisPattern
            
            # Create VisPattern instance from the saved file
            pattern = VisPattern(str(pattern_file))
            pattern.name = pattern_name
            
            # Serialize to generate SVG files (similar to MetaGarment.serialize)
            pattern_folder = pattern.serialize(
                session_dir,
                to_subfolder=True,
                with_3d=False,  # Skip 3D generation for SVG-only
                with_text=with_text,
                view_ids=view_ids,
                with_printable=with_printable,
                empty_ok=True
            )
            pattern_folder = Path(pattern_folder)
            
            # Save body parameters for reference
            body.save(pattern_folder)
            
            # Find generated files
            svg_file = pattern_folder / f'{pattern_name}_pattern.svg'
            png_file = pattern_folder / f'{pattern_name}_pattern.png'
            pdf_file = pattern_folder / f'{pattern_name}_print_pattern.pdf' if with_printable else None
            
            return pattern_folder, svg_file, png_file, pdf_file
                
        except Exception as e:
            logger.error(f"Error generating SVG from pattern specification: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Fallback: try to extract design parameters if available
            if 'design' in pattern_specification:
                logger.info("Falling back to design parameters extraction...")
                design_params = pattern_specification['design']
                return self._generate_svg_from_design_params(design_params, session_dir, body,
                                                           with_text, view_ids, with_printable)
            else:
                raise Exception(f"Could not process pattern specification: {str(e)}")

    def cleanup_session(self, session_id: str):
        """Clean up session files
        
        Args:
            session_id: Session to clean up
        """
        session_dir = self.output_root / session_id
        if session_dir.exists():
            import shutil
            shutil.rmtree(session_dir)

# Initialize the SVG generation service
try:
    svg_service = GarmentSVGService(output_root="./tmp_svg_service")
    logger.info("SVG Generation Service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize SVG Generation Service: {str(e)}")
    logger.error(traceback.format_exc())
    raise

@app.post("/generate3d", response_model=Generate3DResponse)
async def generate_3d(request: Generate3DRequest):
    """Generate 3D files from pattern specification
    
    Args:
        request: Generate3DRequest containing pattern specification and optional body parameters
        
    Returns:
        Generate3DResponse with session ID and file paths
    """
    try:
        logger.info("Received generate3d request")
        logger.debug(f"Pattern specification keys: {list(request.pattern_specification.keys())}")
        if request.body_params:
            logger.debug(f"Body params: {request.body_params}")

        # Generate unique session ID
        session_id = str(uuid.uuid4())
        logger.info(f"Created session ID: {session_id}")
        
        # Generate 3D files
        logger.info("Starting 3D generation from pattern specification")
        output_dir, glb_path = service.generate_3d(
            pattern_specification=request.pattern_specification,
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

# @app.post("/generate3d_legacy", response_model=Generate3DResponse)
# async def generate_3d_legacy(request: LegacyGenerate3DRequest):
#     """Generate 3D files from design parameters (Legacy endpoint for backward compatibility)
    
#     Args:
#         request: LegacyGenerate3DRequest containing design and optional body parameters
        
#     Returns:
#         Generate3DResponse with session ID and file paths
#     """
#     try:
#         logger.info("Received legacy generate3d request")
#         logger.debug(f"Design params: {request.design_params}")
#         if request.body_params:
#             logger.debug(f"Body params: {request.body_params}")

#         # Generate unique session ID
#         session_id = str(uuid.uuid4())
#         logger.info(f"Created session ID: {session_id}")
        
#         # Generate 3D files using legacy method
#         logger.info("Starting 3D generation from design parameters")
#         output_dir, glb_path = service.generate_3d(
#             design_params=request.design_params,
#             session_id=session_id,
#             body_params=request.body_params
#         )
#         logger.info(f"3D generation completed. Output dir: {output_dir}, GLB path: {glb_path}")
        
#         return Generate3DResponse(
#             session_id=session_id,
#             glb_file_path=str(glb_path),
#             output_dir=str(output_dir)
#         )
#     except Exception as e:
#         logger.error(f"Error in generate_3d_legacy: {str(e)}")
#         logger.error(traceback.format_exc())
#         raise HTTPException(status_code=500, detail=f"Error in 3D generation: {str(e)}\n{traceback.format_exc()}")

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

@app.post("/generate_svg", response_model=GenerateSVGResponse)
async def generate_svg(request: GenerateSVGRequest):
    """Generate SVG pattern files from pattern specification or design parameters
    
    Args:
        request: GenerateSVGRequest containing pattern/design data and SVG options
        
    Returns:
        GenerateSVGResponse with session ID and file paths
    """
    try:
        logger.info("Received generate_svg request")
        
        # Validate input
        if not request.pattern_specification and not request.design_params:
            raise HTTPException(status_code=400, detail="Either pattern_specification or design_params must be provided")
        
        if request.pattern_specification:
            logger.debug(f"Pattern specification keys: {list(request.pattern_specification.keys())}")
        if request.design_params:
            logger.debug(f"Design params: {request.design_params}")
        if request.body_params:
            logger.debug(f"Body params: {request.body_params}")

        # Generate unique session ID
        session_id = str(uuid.uuid4())
        logger.info(f"Created SVG session ID: {session_id}")
        
        # Generate SVG files
        logger.info("Starting SVG generation")
        output_dir, svg_path, png_path, pdf_path = svg_service.generate_svg(
            pattern_specification=request.pattern_specification,
            design_params=request.design_params,
            session_id=session_id,
            body_params=request.body_params,
            with_text=request.with_text,
            view_ids=request.view_ids,
            with_printable=request.with_printable
        )
        logger.info(f"SVG generation completed. Output dir: {output_dir}")
        logger.info(f"Generated files - SVG: {svg_path}, PNG: {png_path}, PDF: {pdf_path}")
        
        return GenerateSVGResponse(
            session_id=session_id,
            svg_file_path=str(svg_path),
            png_file_path=str(png_path),
            output_dir=str(output_dir),
            printable_pdf_path=str(pdf_path) if pdf_path else None
        )
    except Exception as e:
        logger.error(f"Error in generate_svg: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error in SVG generation: {str(e)}\n{traceback.format_exc()}")

@app.get("/download_svg/{session_id}")
async def download_svg(session_id: str):
    """Download the generated SVG file
    
    Args:
        session_id: Session ID from generate_svg request
        
    Returns:
        SVG file as attachment
    """
    try:
        logger.info(f"Received SVG download request for session: {session_id}")
        # Find the SVG file in the session directory
        session_dir = Path("./tmp_svg_service") / session_id
        svg_files = list(session_dir.rglob("*.svg"))
        
        # Filter out printable SVG files, get the main pattern SVG
        pattern_svg_files = [f for f in svg_files if '_pattern.svg' in f.name and '_print_pattern.svg' not in f.name]
        
        if not pattern_svg_files:
            logger.error(f"No SVG file found in session {session_id}")
            raise HTTPException(status_code=404, detail="SVG file not found")
            
        logger.info(f"Returning SVG file: {pattern_svg_files[0]}")
        return FileResponse(
            path=str(pattern_svg_files[0]),
            filename=pattern_svg_files[0].name,
            media_type="image/svg+xml"
        )
    except Exception as e:
        logger.error(f"Error in download_svg: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download_png/{session_id}")
async def download_png(session_id: str):
    """Download the generated PNG file
    
    Args:
        session_id: Session ID from generate_svg request
        
    Returns:
        PNG file as attachment
    """
    try:
        logger.info(f"Received PNG download request for session: {session_id}")
        # Find the PNG file in the session directory
        session_dir = Path("./tmp_svg_service") / session_id
        png_files = list(session_dir.rglob("*.png"))
        
        # Filter to get the main pattern PNG (not 3D)
        pattern_png_files = [f for f in png_files if '_pattern.png' in f.name and '_3d_pattern.png' not in f.name]
        
        if not pattern_png_files:
            logger.error(f"No PNG file found in session {session_id}")
            raise HTTPException(status_code=404, detail="PNG file not found")
            
        logger.info(f"Returning PNG file: {pattern_png_files[0]}")
        return FileResponse(
            path=str(pattern_png_files[0]),
            filename=pattern_png_files[0].name,
            media_type="image/png"
        )
    except Exception as e:
        logger.error(f"Error in download_png: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download_pdf/{session_id}")
async def download_pdf(session_id: str):
    """Download the generated printable PDF file
    
    Args:
        session_id: Session ID from generate_svg request
        
    Returns:
        PDF file as attachment
    """
    try:
        logger.info(f"Received PDF download request for session: {session_id}")
        # Find the PDF file in the session directory
        session_dir = Path("./tmp_svg_service") / session_id
        pdf_files = list(session_dir.rglob("*.pdf"))
        
        if not pdf_files:
            logger.error(f"No PDF file found in session {session_id}")
            raise HTTPException(status_code=404, detail="PDF file not found")
            
        logger.info(f"Returning PDF file: {pdf_files[0]}")
        return FileResponse(
            path=str(pdf_files[0]),
            filename=pdf_files[0].name,
            media_type="application/pdf"
        )
    except Exception as e:
        logger.error(f"Error in download_pdf: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
        
@app.delete("/cleanup_svg/{session_id}")
async def cleanup_svg_session(session_id: str):
    """Clean up SVG session files
    
    Args:
        session_id: SVG session to clean up
    """
    try:
        logger.info(f"Cleaning up SVG session: {session_id}")
        svg_service.cleanup_session(session_id)
        logger.info(f"Successfully cleaned up SVG session: {session_id}")
        return {"status": "success", "message": f"SVG Session {session_id} cleaned up"}
    except Exception as e:
        logger.error(f"Error in cleanup_svg_session: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
        
@app.post("/generate_pattern_svg", response_model=GenerateSVGResponse)
async def generate_pattern_svg(request: Generate3DRequest):
    """Generate SVG pattern files directly from pattern specification (like generate3d endpoint)
    
    This endpoint works exactly like generate3d but produces SVG files instead of 3D files.
    It takes the same input format as generate3d for consistency.
    
    Args:
        request: Generate3DRequest containing pattern specification and optional body parameters
        
    Returns:
        GenerateSVGResponse with session ID and file paths
    """
    try:
        logger.info("Received generate_pattern_svg request")
        logger.debug(f"Pattern specification keys: {list(request.pattern_specification.keys())}")
        if request.body_params:
            logger.debug(f"Body params: {request.body_params}")

        # Generate unique session ID
        session_id = str(uuid.uuid4())
        logger.info(f"Created pattern SVG session ID: {session_id}")
        
        # Generate SVG files directly from pattern specification
        logger.info("Starting SVG generation from pattern specification")
        output_dir, svg_path, png_path, pdf_path = svg_service.generate_svg(
            pattern_specification=request.pattern_specification,
            session_id=session_id,
            body_params=request.body_params,
            with_text=True,  # Default to showing text
            view_ids=False,  # Default to not showing IDs for cleaner output
            with_printable=True  # Default to generating printable version
        )
        logger.info(f"Pattern SVG generation completed. Output dir: {output_dir}")
        logger.info(f"Generated files - SVG: {svg_path}, PNG: {png_path}, PDF: {pdf_path}")
        
        return GenerateSVGResponse(
            session_id=session_id,
            svg_file_path=str(svg_path),
            png_file_path=str(png_path),
            output_dir=str(output_dir),
            printable_pdf_path=str(pdf_path) if pdf_path else None
        )
    except Exception as e:
        logger.error(f"Error in generate_pattern_svg: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error in pattern SVG generation: {str(e)}\n{traceback.format_exc()}")
        
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")