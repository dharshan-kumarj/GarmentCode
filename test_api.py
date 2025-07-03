import requests
import json

# Test data
test_data = {
    "design_params": {
        "meta": {
            "upper": {"v": "FittedShirt", "type": "select_null", "range": ["FittedShirt", "Shirt", None], "default_prob": 0.3},
            "bottom": {"v": None, "type": "select_null", "range": ["SkirtCircle", "AsymmSkirtCircle", "GodetSkirt", "Pants", "Skirt2", "SkirtManyPanels", "PencilSkirt", "SkirtLevels", None], "default_prob": 0.3},
            "wb": {"v": None, "type": "select_null", "range": ["StraightWB", "FittedWB", None], "default_prob": 0.5}
        },
        "shirt": {
            "width": {"v": 1.05, "type": "float", "range": [1.0, 1.3], "default_prob": 0.4},
            "strapless": {"v": False, "type": "bool", "range": [True, False], "default_prob": 0.8},
            "length": {"v": 1.2, "type": "float", "range": [0.5, 3.5], "default_prob": 0.7},
            "flare": {"v": 1.0, "type": "float", "range": [0.7, 1.6], "default_prob": 0.4}
        },
        "sleeve": {
            "sleeveless": {"v": True, "type": "bool", "range": [True, False], "default_prob": 0.7},
            "armhole_shape": {"v": "ArmholeCurve", "type": "select", "range": ["ArmholeSquare", "ArmholeAngle", "ArmholeCurve"], "default_prob": 0.7},
            "length": {"v": 0.3, "type": "float", "range": [0.1, 1.15]},
            "connecting_width": {"v": 0.2, "type": "float", "range": [0, 2], "default_prob": 0.6},
            "end_width": {"v": 1.0, "type": "float", "range": [0.2, 2], "default_prob": 0.4},
            "sleeve_angle": {"v": 10, "type": "int", "range": [10, 50]},
            "smoothing_coeff": {"v": 0.25, "type": "float", "range": [0.1, 0.4], "default_prob": 0.8},
            "opening_dir_mix": {"v": 0.1, "type": "float", "range": [-0.9, 0.8], "default_prob": 1.0},
            "standing_shoulder": {"v": False, "type": "bool", "range": [True, False], "default_prob": 0.8},
            "standing_shoulder_len": {"v": 5.0, "type": "float", "range": [4, 10]},
            "connect_ruffle": {"v": 1, "type": "float", "range": [1, 2], "default_prob": 0.4},
            "cuff": {
                "type": {"v": None, "type": "select_null", "range": ["CuffBand", "CuffSkirt", "CuffBandSkirt", None]},
                "cuff_len": {"v": 0.1, "type": "float", "range": [0.05, 0.9], "default_prob": 0.7},
                "skirt_flare": {"v": 1.2, "type": "float", "range": [1, 2]},
                "skirt_fraction": {"v": 0.5, "type": "float", "range": [0.1, 0.9], "default_prob": 0.5},
                "skirt_ruffle": {"v": 1.0, "type": "float", "range": [1, 1.5], "default_prob": 0.3},
                "top_ruffle": {"v": 1, "type": "float", "range": [1, 3]}
            }
        },
        "collar": {
            "f_collar": {"v": "CircleNeckHalf", "type": "select", "range": ["CircleNeckHalf", "CurvyNeckHalf", "VNeckHalf", "SquareNeckHalf", "TrapezoidNeckHalf", "CircleArcNeckHalf", "Bezier2NeckHalf"], "default_prob": 0.4},
            "b_collar": {"v": "CircleNeckHalf", "type": "select", "range": ["CircleNeckHalf", "CurvyNeckHalf", "VNeckHalf", "SquareNeckHalf", "TrapezoidNeckHalf", "CircleArcNeckHalf", "Bezier2NeckHalf"], "default_prob": 0.8},
            "width": {"v": 0.2, "type": "float", "range": [-0.5, 1], "default_prob": 0.4},
            "fc_depth": {"v": 0.4, "type": "float", "range": [0.3, 2], "default_prob": 0.3},
            "bc_depth": {"v": 0, "type": "float", "range": [0, 2], "default_prob": 0.4},
            "fc_angle": {"v": 95, "type": "int", "range": [70, 110]},
            "bc_angle": {"v": 95, "type": "int", "range": [70, 110]},
            "f_bezier_x": {"v": 0.3, "type": "float", "range": [0.05, 0.95], "default_prob": 0.4},
            "f_bezier_y": {"v": 0.55, "type": "float", "range": [0.05, 0.95], "default_prob": 0.4},
            "b_bezier_x": {"v": 0.15, "type": "float", "range": [0.05, 0.95], "default_prob": 0.4},
            "b_bezier_y": {"v": 0.1, "type": "float", "range": [0.05, 0.95]},
            "f_flip_curve": {"v": False, "type": "bool", "range": [True, False], "default_prob": 0.8},
            "b_flip_curve": {"v": False, "type": "bool", "range": [True, False], "default_prob": 0.8},
            "component": {
                "style": {"v": None, "type": "select_null", "range": ["Turtle", "SimpleLapel", "Hood2Panels", None], "default_prob": 0.6},
                "depth": {"v": 7, "type": "int", "range": [2, 8]},
                "lapel_standing": {"v": False, "type": "bool", "range": [True, False]},
                "hood_depth": {"v": 1, "type": "float", "range": [1, 2], "default_prob": 0.6},
                "hood_length": {"v": 1, "type": "float", "range": [1, 1.5], "default_prob": 0.6}
            }
        },
        "left": {
            "enable_asym": {"v": False, "type": "bool", "range": [True, False], "default_prob": 0.8},
            "shirt": {
                "strapless": {"v": False, "type": "bool", "range": [True, False], "default_prob": 0.8},
                "width": {"v": 1.05, "type": "float", "range": [1.0, 1.3], "default_prob": 0.4},
                "flare": {"v": 1.0, "type": "float", "range": [0.7, 1.6], "default_prob": 0.4}
            },
            "sleeve": {
                "sleeveless": {"v": True, "type": "bool", "range": [True, False], "default_prob": 0.7},
                "armhole_shape": {"v": "ArmholeCurve", "type": "select", "range": ["ArmholeSquare", "ArmholeAngle", "ArmholeCurve"], "default_prob": 0.7},
                "length": {"v": 0.3, "type": "float", "range": [0.1, 1.15]},
                "connecting_width": {"v": 0.2, "type": "float", "range": [0, 2], "default_prob": 0.6},
                "end_width": {"v": 1.0, "type": "float", "range": [0.2, 2], "default_prob": 0.4},
                "sleeve_angle": {"v": 10, "type": "int", "range": [10, 50]},
                "smoothing_coeff": {"v": 0.25, "type": "float", "range": [0.1, 0.4], "default_prob": 0.8},
                "opening_dir_mix": {"v": 0.1, "type": "float", "range": [-0.9, 0.8], "default_prob": 1.0}
            },
            "collar": {
                "width": {"v": 0.2, "type": "float", "range": [0, 1], "default_prob": 0.4},
                "f_collar": {"v": "CircleNeckHalf", "type": "select", "range": ["CircleNeckHalf", "CurvyNeckHalf", "VNeckHalf", "SquareNeckHalf", "TrapezoidNeckHalf", "CircleArcNeckHalf", "Bezier2NeckHalf"], "default_prob": 0.4},
                "b_collar": {"v": "CircleNeckHalf", "type": "select", "range": ["CircleNeckHalf", "CurvyNeckHalf", "VNeckHalf", "SquareNeckHalf", "TrapezoidNeckHalf", "CircleArcNeckHalf", "Bezier2NeckHalf"], "default_prob": 0.8},
                "f_bezier_x": {"v": 0.3, "type": "float", "range": [0.05, 0.95], "default_prob": 0.4},
                "f_bezier_y": {"v": 0.55, "type": "float", "range": [0.05, 0.95]},
                "b_bezier_x": {"v": 0.15, "type": "float", "range": [0.05, 0.95], "default_prob": 0.4},
                "b_bezier_y": {"v": 0.1, "type": "float", "range": [0.05, 0.95]},
                "f_flip_curve": {"v": False, "type": "bool", "range": [True, False], "default_prob": 0.8},
                "b_flip_curve": {"v": False, "type": "bool", "range": [True, False], "default_prob": 0.8},
                "fc_angle": {"v": 95, "type": "int", "range": [70, 110]},
                "bc_angle": {"v": 95, "type": "int", "range": [70, 110]}
            }
        }
    }
}

# Make the request
try:
    response = requests.post(
        "http://localhost:8000/generate3d",
        json=test_data
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2) if response.ok else response.text}")
except Exception as e:
    print(f"Error: {str(e)}")
