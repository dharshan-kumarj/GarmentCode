"""Simple web interface for rendering 3D body and dress models"""

import asyncio
from pathlib import Path
import numpy as np
from nicegui import ui, app, Client
import json
from fastapi import HTTPException
import shutil

# Constants
SCENE_RESOLUTION = (1024, 800)
CAMERA_FOV = 30  # degrees
CAMERA_LOCATION = [0, -4.15, 1.25]
BG_COLOR = '#ffffff'

class Simple3DRenderer:
    def __init__(self):
        # Setup static file paths
        self.path_static_3d = '/geo'
        self.path_static_body = '/body'
        self.local_path_3d = Path('./tmp_3d_render/garm_3d')
        self.local_path_body = Path('./assets/bodies')
        self.default_garment = Path('/root/sagar/GarmentCode/tmp_gui/garm_3d/uploaded_garment.glb')
        
        # Create directories
        self.local_path_3d.mkdir(parents=True, exist_ok=True)
        
        # Add static file mappings
        app.add_static_files(self.path_static_3d, self.local_path_3d)
        app.add_static_files(self.path_static_body, self.local_path_body)
        
        # UI elements
        self.ui_3d_scene = None
        self.ui_body_3d = None
        self.ui_garment_3d = None
        self.ui_body_switch = None
        
        # State tracking
        self.current_garment = None
        self.body_visible = True

    def create_lights(self, scene: ui.scene, intensity=30.0):
        """Add lights to the scene"""
        light_positions = np.array([
            [1.60614, 1.23701, 1.5341],
            [1.31844, -2.52238, 1.92831],
            [-2.80522, 2.34624, 1.2594],
            [0.160261, 3.52215, 1.81789],
            [-2.65752, -1.26328, 1.41194]
        ])
        light_colors = ['#ffffff'] * 5
        z_dirs = np.arctan2(light_positions[:, 1], light_positions[:, 0])

        for i in range(len(light_positions)):
            scene.spot_light(
                color=light_colors[i], 
                intensity=intensity,
                angle=np.pi,
            ).rotate(0., 0., -z_dirs[i]).move(
                light_positions[i][0], 
                light_positions[i][1], 
                light_positions[i][2]
            )

    def setup_camera(self, scene):
        """Setup camera in the scene"""
        camera = scene.perspective_camera(fov=CAMERA_FOV)
        camera.x = CAMERA_LOCATION[0]
        camera.y = CAMERA_LOCATION[1]
        camera.z = CAMERA_LOCATION[2]
        
        # Set look at point
        camera.look_at_x = 0
        camera.look_at_y = 0
        camera.look_at_z = CAMERA_LOCATION[2] * 2/3

    def setup_ui(self):
        """Setup the web interface"""
        # Header
        with ui.header(elevated=True).classes('items-center justify-end py-0 px-4 m-0'):
            ui.label('3D Garment Viewer').classes('mr-auto').style('font-size: 150%; font-weight: 400')
        
        # Main content
        with ui.column().classes('w-full h-full p-4'):
            # Controls
            with ui.row().classes('w-full justify-between items-center mb-4'):
                self.ui_body_switch = ui.switch(
                    'Show Body', 
                    value=True,
                    on_change=lambda e: self.ui_body_3d.visible(e.value)
                ).props('dense left-label')
                
                ui.button('Load Garment', on_click=self.load_garment).props('color=primary')
            
            # 3D Scene
            with ui.scene(
                width=SCENE_RESOLUTION[0],
                height=SCENE_RESOLUTION[1],
                grid=False,
                background_color=BG_COLOR
            ).classes('w-full h-[80vh]') as self.ui_3d_scene:
                
                # Setup camera
                self.setup_camera(self.ui_3d_scene)
                
                # Add lights
                self.create_lights(self.ui_3d_scene, intensity=60.)
                
                # Add body model
                self.ui_body_3d = self.ui_3d_scene.stl(
                    '/body/mean_all.stl'
                ).rotate(np.pi / 2, 0., 0.).material(color='#000000')

        # Footer
        with ui.footer().classes('items-center justify-center p-0 m-0'):
            ui.label('© 2024 Interactive Geometry Lab')

    async def load_garment(self):
        """Handle garment file upload and rendering"""
        async def handle_upload(e):
            try:
                # Save uploaded file
                file_path = self.local_path_3d / 'uploaded_garment.glb'
                with open(file_path, 'wb') as f:
                    f.write(e.content.read())
                
                # Update 3D scene
                if self.ui_garment_3d is not None:
                    self.ui_garment_3d.delete()
                
                with self.ui_3d_scene:
                    self.ui_garment_3d = self.ui_3d_scene.gltf(
                        f'{self.path_static_3d}/uploaded_garment.glb'
                    ).scale(0.01).rotate(np.pi / 2, 0., 0.)
                
                self.current_garment = str(file_path)
                ui.notify('Garment loaded successfully!')
                
            except Exception as e:
                ui.notify(f'Error loading garment: {str(e)}', type='negative')
            
            finally:
                dialog.close()

        # Create upload dialog
        with ui.dialog() as dialog, ui.card().classes('items-center'):
            ui.label('Upload Garment Model (GLB format)')
            ui.upload(
                label='Choose GLB file',
                on_upload=handle_upload
            ).props('accept=.glb')
            ui.button('Cancel', on_click=dialog.close)

    async def load_default_garment(self):
        """Load the default garment model"""
        try:
            if self.default_garment.exists():
                # Copy default garment to static directory
                target_path = self.local_path_3d / 'uploaded_garment.glb'
                shutil.copy2(self.default_garment, target_path)
                
                # Update 3D scene
                if self.ui_garment_3d is not None:
                    self.ui_garment_3d.delete()
                
                with self.ui_3d_scene:
                    self.ui_garment_3d = self.ui_3d_scene.gltf(
                        f'{self.path_static_3d}/uploaded_garment.glb'
                    ).scale(0.01).rotate(np.pi / 2, 0., 0.)
                
                self.current_garment = str(target_path)
                print("Default garment loaded successfully")
            else:
                print(f"Default garment not found at {self.default_garment}")
        except Exception as e:
            print(f"Error loading default garment: {str(e)}")

    def setup_endpoints(self):
        """Setup API endpoints"""
        @app.post('/api/load_garment')
        async def load_garment_endpoint(file_path: str):
            try:
                garment_path = Path(file_path)
                if not garment_path.exists():
                    raise HTTPException(status_code=404, detail="Garment file not found")
                
                if garment_path.suffix.lower() != '.glb':
                    raise HTTPException(status_code=400, detail="Only GLB files are supported")
                
                target_path = self.local_path_3d / 'uploaded_garment.glb'
                shutil.copy2(garment_path, target_path)
                
                if self.ui_garment_3d is not None:
                    self.ui_garment_3d.delete()
                
                with self.ui_3d_scene:
                    self.ui_garment_3d = self.ui_3d_scene.gltf(
                        f'{self.path_static_3d}/uploaded_garment.glb'
                    ).scale(0.01).rotate(np.pi / 2, 0., 0.)
                
                self.current_garment = str(target_path)
                return {"status": "success", "message": "Garment loaded successfully"}
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.post('/api/toggle_body')
        async def toggle_body_endpoint(visible: bool = None):
            try:
                if visible is None:
                    self.body_visible = not self.body_visible
                else:
                    self.body_visible = visible
                
                self.ui_body_3d.visible(self.body_visible)
                self.ui_body_switch.set_value(self.body_visible)
                
                return {
                    "status": "success", 
                    "body_visible": self.body_visible
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.get('/api/state')
        async def get_state():
            try:
                return {
                    "status": "success",
                    "body_visible": self.body_visible,
                    "current_garment": self.current_garment,
                    "camera": {
                        "fov": CAMERA_FOV,
                        "location": CAMERA_LOCATION
                    }
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.post('/api/reset')
        async def reset_viewer():
            try:
                if self.ui_garment_3d is not None:
                    self.ui_garment_3d.delete()
                    self.ui_garment_3d = None
                
                self.body_visible = True
                self.ui_body_3d.visible(True)
                self.ui_body_switch.set_value(True)
                
                self.current_garment = None
                
                return {"status": "success", "message": "Viewer reset successfully"}
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

@ui.page('/')
async def index(client: Client):
    # Initialize renderer
    renderer = Simple3DRenderer()
    
    # Setup UI
    renderer.setup_ui()
    renderer.setup_endpoints()
    
    # Load default garment after UI is ready
    await renderer.load_default_garment()
    
    # Handle client disconnect
    await client.disconnected()
    print('Client disconnected. Cleaning up...')

def main():
    """Main entry point"""
    ui.run(
        title='3D Garment Viewer',
        port=8001,
        host='0.0.0.0',  # Allow external access
        reload=False
    )

if __name__ in {"__main__", "__mp_main__"}:
    main() 