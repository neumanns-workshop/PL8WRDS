"""
Interactive Map Pinning System for Geographic Flight Paths.

This router provides a visual interface for pinning locations on the 1918 vintage map
and exporting them for use in the dynamic flight path system.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/map", tags=["map-pinning"])

# Data models
class MapPin(BaseModel):
    """Represents a pinned location on the vintage map."""
    id: str = Field(..., description="Unique identifier for the pin")
    name: str = Field(..., description="Location name (e.g., 'New York', 'Chicago')")
    x_percent: float = Field(..., ge=0, le=100, description="X position as percentage of map width")
    y_percent: float = Field(..., ge=0, le=100, description="Y position as percentage of map height")
    category: str = Field(default="city", description="Pin category: city, landmark, junction, etc.")
    notes: Optional[str] = Field(None, description="Optional notes about this location")
    created_at: datetime = Field(default_factory=datetime.now)

class FlightRoute(BaseModel):
    """Represents a flight route between pinned locations."""
    id: str = Field(..., description="Unique route identifier")
    name: str = Field(..., description="Route name (e.g., 'Transcontinental Express')")
    waypoints: List[str] = Field(..., description="List of pin IDs defining the route path")
    duration_seconds: int = Field(..., gt=0, description="Animation duration in seconds")
    description: Optional[str] = Field(None, description="Route description")

class MapConfiguration(BaseModel):
    """Complete map configuration with pins and routes."""
    pins: List[MapPin] = Field(default_factory=list)
    routes: List[FlightRoute] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    version: str = Field(default="1.0")

# Storage paths
MAP_DATA_DIR = Path("cache/map_data")
MAP_DATA_DIR.mkdir(exist_ok=True)
PINS_FILE = MAP_DATA_DIR / "map_pins.json"
ROUTES_FILE = MAP_DATA_DIR / "flight_routes.json"

# Utility functions
def load_pins() -> List[MapPin]:
    """Load pins from storage."""
    if not PINS_FILE.exists():
        return []
    try:
        with open(PINS_FILE, 'r') as f:
            data = json.load(f)
        return [MapPin(**pin) for pin in data]
    except Exception as e:
        logger.error(f"Error loading pins: {e}")
        return []

def save_pins(pins: List[MapPin]) -> None:
    """Save pins to storage."""
    try:
        with open(PINS_FILE, 'w') as f:
            json.dump([pin.dict() for pin in pins], f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error saving pins: {e}")
        raise

def load_routes() -> List[FlightRoute]:
    """Load routes from storage."""
    if not ROUTES_FILE.exists():
        return []
    try:
        with open(ROUTES_FILE, 'r') as f:
            data = json.load(f)
        return [FlightRoute(**route) for route in data]
    except Exception as e:
        logger.error(f"Error loading routes: {e}")
        return []

def save_routes(routes: List[FlightRoute]) -> None:
    """Save routes to storage."""
    try:
        with open(ROUTES_FILE, 'w') as f:
            json.dump([route.dict() for route in routes], f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error saving routes: {e}")
        raise


# API Endpoints
@router.get("/", response_class=HTMLResponse)
async def map_pinning_interface():
    """Serve the interactive map pinning interface."""
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PL8WRDS - Vintage Map Pinning Interface</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Inter', system-ui, -apple-system, sans-serif;
                background: #F5F1E8;
                color: #2C3E50;
                line-height: 1.6;
            }}
            
            .header {{
                background: #1B4F72;
                color: white;
                padding: 1rem 2rem;
                border-bottom: 4px solid #C0392B;
            }}
            
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                padding: 2rem;
            }}
            
            .map-container {{
                position: relative;
                border: 3px solid #BDC3C7;
                border-radius: 8px;
                overflow: hidden;
                margin-bottom: 2rem;
                background: white;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
            }}
            
            #vintage-map {{
                width: 100%;
                height: auto;
                display: block;
                cursor: crosshair;
            }}
            
            .pin {{
                position: absolute;
                width: 24px;
                height: 24px;
                background: #C0392B;
                border: 3px solid white;
                border-radius: 50%;
                cursor: pointer;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
                transform: translate(-50%, -50%);
                z-index: 10;
                transition: all 0.2s ease;
            }}
            
            .pin:hover {{
                background: #E74C3C;
                transform: translate(-50%, -50%) scale(1.2);
            }}
            
            .pin.landmark {{
                background: #27AE60;
            }}
            
            .pin.junction {{
                background: #F39C12;
            }}
            
            .pin-label {{
                position: absolute;
                bottom: 100%;
                left: 50%;
                transform: translateX(-50%);
                background: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                white-space: nowrap;
                opacity: 0;
                transition: opacity 0.2s ease;
                pointer-events: none;
            }}
            
            .pin:hover .pin-label {{
                opacity: 1;
            }}
            
            .controls {{
                display: grid;
                grid-template-columns: 1fr 1fr 1fr;
                gap: 2rem;
                margin-bottom: 2rem;
            }}
            
            .control-panel {{
                background: white;
                padding: 1.5rem;
                border-radius: 8px;
                border: 2px solid #BDC3C7;
            }}
            
            .control-panel h3 {{
                color: #1B4F72;
                margin-bottom: 1rem;
                border-bottom: 2px solid #E8E8E8;
                padding-bottom: 0.5rem;
            }}
            
            .form-group {{
                margin-bottom: 1rem;
            }}
            
            .form-group label {{
                display: block;
                margin-bottom: 0.5rem;
                font-weight: 500;
            }}
            
            .form-group input, .form-group select {{
                width: 100%;
                padding: 0.5rem;
                border: 2px solid #E8E8E8;
                border-radius: 4px;
                font-size: 14px;
            }}
            
            .form-group input:focus, .form-group select:focus {{
                outline: none;
                border-color: #1B4F72;
            }}
            
            .btn {{
                background: #1B4F72;
                color: white;
                border: none;
                padding: 0.75rem 1.5rem;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                transition: background 0.2s ease;
                margin-right: 0.5rem;
                margin-bottom: 0.5rem;
            }}
            
            .btn:hover {{
                background: #2E6DA4;
            }}
            
            .btn.secondary {{
                background: #27AE60;
            }}
            
            .btn.secondary:hover {{
                background: #2ECC71;
            }}
            
            .btn.danger {{
                background: #C0392B;
            }}
            
            .btn.danger:hover {{
                background: #E74C3C;
            }}
            
            .pin-list {{
                max-height: 300px;
                overflow-y: auto;
                border: 1px solid #E8E8E8;
                border-radius: 4px;
            }}
            
            .pin-item {{
                padding: 0.75rem;
                border-bottom: 1px solid #F0F0F0;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            
            .pin-item:last-child {{
                border-bottom: none;
            }}
            
            .pin-item:hover {{
                background: #F8F9FA;
            }}
            
            .pin-info {{
                flex: 1;
            }}
            
            .pin-name {{
                font-weight: 500;
                color: #1B4F72;
            }}
            
            .pin-coords {{
                font-size: 12px;
                color: #7F8C8D;
            }}
            
            .output {{
                background: #2C3E50;
                color: #E8E8E8;
                padding: 1rem;
                border-radius: 4px;
                font-family: 'Monaco', 'Consolas', monospace;
                font-size: 12px;
                max-height: 200px;
                overflow-y: auto;
                white-space: pre-wrap;
                margin-top: 1rem;
            }}
            
            .instructions {{
                background: #E8F4F8;
                border: 1px solid #85C1E9;
                border-radius: 4px;
                padding: 1rem;
                margin-bottom: 2rem;
            }}
            
            .instructions h4 {{
                color: #1B4F72;
                margin-bottom: 0.5rem;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🗺️ PL8WRDS Vintage Map Pinning Interface</h1>
            <p>Pin locations on the 1918 AAA map to create realistic flight paths</p>
        </div>
        
        <div class="container">
            <div class="instructions">
                <h4>Instructions:</h4>
                <ul>
                    <li><strong>Click on the map</strong> to add a new pin at that location</li>
                    <li><strong>Click on existing pins</strong> to select and edit them</li>
                    <li><strong>Choose pin categories:</strong> City (red), Landmark (green), Junction (orange)</li>
                    <li><strong>Export your configuration</strong> when ready to use in the flight path system</li>
                </ul>
            </div>
            
            <div class="map-container">
                <img id="vintage-map" src="/map/image" alt="1918 AAA Vintage Map">
                <div id="pins-layer"></div>
            </div>
            
            <div class="controls">
                <div class="control-panel">
                    <h3>🎯 Add/Edit Pin</h3>
                    <div class="form-group">
                        <label for="pin-name">Location Name:</label>
                        <input type="text" id="pin-name" placeholder="e.g., New York City">
                    </div>
                    <div class="form-group">
                        <label for="pin-category">Category:</label>
                        <select id="pin-category">
                            <option value="city">🏙️ Major City</option>
                            <option value="landmark">🏔️ Landmark</option>
                            <option value="junction">🛣️ Junction</option>
                            <option value="airport">✈️ Airport</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="pin-notes">Notes (optional):</label>
                        <input type="text" id="pin-notes" placeholder="Additional info...">
                    </div>
                    <button class="btn" onclick="saveCurrentPin()">💾 Save Pin</button>
                    <button class="btn danger" onclick="deleteCurrentPin()">🗑️ Delete</button>
                </div>
                
                <div class="control-panel">
                    <h3>📍 Pin List</h3>
                    <div id="pin-list" class="pin-list">
                        <!-- Pins will be listed here -->
                    </div>
                    <button class="btn secondary" onclick="loadPins()">🔄 Refresh</button>
                    <button class="btn danger" onclick="clearAllPins()">🗑️ Clear All</button>
                </div>
                
                <div class="control-panel">
                    <h3>📤 Export</h3>
                    <button class="btn" onclick="exportForDynamicBackground()">📄 Export for Flight Paths</button>
                    <button class="btn secondary" onclick="exportRawJSON()">💾 Export Raw JSON</button>
                    <button class="btn" onclick="importConfiguration()">📥 Import Config</button>
                    <input type="file" id="import-file" accept=".json" style="display: none;">
                    <div id="export-output" class="output" style="display: none;"></div>
                </div>
            </div>
        </div>
        
        <script>
            let pins = [];
            let currentPin = null;
            let mapImg = null;
            
            // Initialize when page loads
            document.addEventListener('DOMContentLoaded', function() {{
                mapImg = document.getElementById('vintage-map');
                loadPins();
                
                // Add click handler to map
                mapImg.addEventListener('click', handleMapClick);
            }});
            
            function handleMapClick(event) {{
                const rect = mapImg.getBoundingClientRect();
                const x = event.clientX - rect.left;
                const y = event.clientY - rect.top;
                const xPercent = (x / rect.width) * 100;
                const yPercent = (y / rect.height) * 100;
                
                // Create new pin
                const pinId = 'pin_' + Date.now();
                const newPin = {{
                    id: pinId,
                    name: 'New Location',
                    x_percent: xPercent,
                    y_percent: yPercent,
                    category: 'city',
                    notes: '',
                    created_at: new Date().toISOString()
                }};
                
                selectPin(newPin);
                renderPins();
            }}
            
            function selectPin(pin) {{
                currentPin = pin;
                document.getElementById('pin-name').value = pin.name || '';
                document.getElementById('pin-category').value = pin.category || 'city';
                document.getElementById('pin-notes').value = pin.notes || '';
                
                // Add to pins array if not already there
                if (!pins.find(p => p.id === pin.id)) {{
                    pins.push(pin);
                }}
                
                renderPins();
            }}
            
            function saveCurrentPin() {{
                if (!currentPin) return;
                
                currentPin.name = document.getElementById('pin-name').value || 'Unnamed Location';
                currentPin.category = document.getElementById('pin-category').value;
                currentPin.notes = document.getElementById('pin-notes').value;
                
                // Save to server
                savePinsToServer();
                renderPins();
                updatePinList();
            }}
            
            function deleteCurrentPin() {{
                if (!currentPin) return;
                
                pins = pins.filter(p => p.id !== currentPin.id);
                currentPin = null;
                
                // Clear form
                document.getElementById('pin-name').value = '';
                document.getElementById('pin-notes').value = '';
                
                savePinsToServer();
                renderPins();
                updatePinList();
            }}
            
            function renderPins() {{
                const pinsLayer = document.getElementById('pins-layer');
                pinsLayer.innerHTML = '';
                
                pins.forEach(pin => {{
                    const pinElement = document.createElement('div');
                    pinElement.className = `pin ${{pin.category}}`;
                    pinElement.style.left = pin.x_percent + '%';
                    pinElement.style.top = pin.y_percent + '%';
                    
                    const label = document.createElement('div');
                    label.className = 'pin-label';
                    label.textContent = pin.name;
                    pinElement.appendChild(label);
                    
                    pinElement.addEventListener('click', (e) => {{
                        e.stopPropagation();
                        selectPin(pin);
                    }});
                    
                    pinsLayer.appendChild(pinElement);
                }});
                
                // Highlight current pin
                if (currentPin) {{
                    const currentPinElement = pinsLayer.querySelector(`[style*="${{currentPin.x_percent}}%"][style*="${{currentPin.y_percent}}%"]`);
                    if (currentPinElement) {{
                        currentPinElement.style.boxShadow = '0 0 0 4px #F39C12';
                    }}
                }}
            }}
            
            function updatePinList() {{
                const pinListContainer = document.getElementById('pin-list');
                pinListContainer.innerHTML = '';
                
                pins.forEach(pin => {{
                    const pinItem = document.createElement('div');
                    pinItem.className = 'pin-item';
                    pinItem.innerHTML = `
                        <div class="pin-info">
                            <div class="pin-name">${{pin.name}}</div>
                            <div class="pin-coords">${{pin.x_percent.toFixed(1)}}%, ${{pin.y_percent.toFixed(1)}}% - ${{pin.category}}</div>
                        </div>
                    `;
                    
                    pinItem.addEventListener('click', () => selectPin(pin));
                    pinListContainer.appendChild(pinItem);
                }});
            }}
            
            async function loadPins() {{
                try {{
                    const response = await fetch('/map/pins');
                    pins = await response.json();
                    renderPins();
                    updatePinList();
                }} catch (error) {{
                    console.error('Failed to load pins:', error);
                }}
            }}
            
            async function savePinsToServer() {{
                try {{
                    await fetch('/map/pins', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify(pins)
                    }});
                }} catch (error) {{
                    console.error('Failed to save pins:', error);
                }}
            }}
            
            function clearAllPins() {{
                if (confirm('Are you sure you want to delete all pins?')) {{
                    pins = [];
                    currentPin = null;
                    savePinsToServer();
                    renderPins();
                    updatePinList();
                }}
            }}
            
            async function exportForDynamicBackground() {{
                const output = document.getElementById('export-output');
                
                // Generate TypeScript interface for DynamicMapBackground
                let tsCode = `// Generated Map Waypoints for PL8WRDS Dynamic Background
// Generated on ${{new Date().toISOString()}}

interface MapWaypoint {{
  id: string;
  name: string;
  x_percent: number;
  y_percent: number;
  category: 'city' | 'landmark' | 'junction' | 'airport';
}}

export const VINTAGE_MAP_WAYPOINTS: MapWaypoint[] = [
`;
                
                pins.forEach(pin => {{
                    tsCode += `  {{
    id: '${{pin.id}}',
    name: '${{pin.name}}',
    x_percent: ${{pin.x_percent.toFixed(2)}},
    y_percent: ${{pin.y_percent.toFixed(2)}},
    category: '${{pin.category}}'
  }},
`;
                }});
                
                tsCode += `];

// Example usage in CSS animation keyframes:
// @keyframes flightPath1 {{
//   0% {{ background-position: ${{pins[0]?.x_percent.toFixed(1) || 50}}% ${{pins[0]?.y_percent.toFixed(1) || 50}}%; }}
//   100% {{ background-position: ${{pins[1]?.x_percent.toFixed(1) || 50}}% ${{pins[1]?.y_percent.toFixed(1) || 50}}%; }}
// }}`;
                
                output.textContent = tsCode;
                output.style.display = 'block';
                
                // Create download
                const blob = new Blob([tsCode], {{ type: 'text/typescript' }});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'vintage-map-waypoints.ts';
                a.click();
                URL.revokeObjectURL(url);
            }}
            
            function exportRawJSON() {{
                const output = document.getElementById('export-output');
                const jsonData = JSON.stringify({{ pins, exported_at: new Date().toISOString() }}, null, 2);
                
                output.textContent = jsonData;
                output.style.display = 'block';
                
                // Create download
                const blob = new Blob([jsonData], {{ type: 'application/json' }});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'map-configuration.json';
                a.click();
                URL.revokeObjectURL(url);
            }}
            
            function importConfiguration() {{
                document.getElementById('import-file').click();
            }}
            
            document.getElementById('import-file').addEventListener('change', function(event) {{
                const file = event.target.files[0];
                if (!file) return;
                
                const reader = new FileReader();
                reader.onload = function(e) {{
                    try {{
                        const data = JSON.parse(e.target.result);
                        pins = data.pins || data; // Support both formats
                        savePinsToServer();
                        renderPins();
                        updatePinList();
                    }} catch (error) {{
                        alert('Failed to import configuration: ' + error.message);
                    }}
                }};
                reader.readAsText(file);
            }});
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.get("/image")
async def get_vintage_map():
    """Serve the vintage map image."""
    # Try to find the vintage map in the React app assets first
    react_map_path = Path("pl8wrds-game/src/assets/1918_AAA_General_Map_of_Transcontinental_Routes.jpg")
    
    # Also try a backend assets directory
    backend_map_path = Path("app/assets/1918_AAA_General_Map_of_Transcontinental_Routes.jpg")
    
    if react_map_path.exists():
        return FileResponse(react_map_path, media_type="image/jpeg")
    elif backend_map_path.exists():
        return FileResponse(backend_map_path, media_type="image/jpeg")
    
    # Fallback: return a 404 with instructions
    raise HTTPException(
        status_code=404, 
        detail={
            "error": "Vintage map image not found",
            "message": "Please ensure the 1918 AAA General Map image exists in one of these locations:",
            "locations": [
                str(react_map_path.absolute()),
                str(backend_map_path.absolute())
            ],
            "note": "You can copy it from pl8wrds-game/src/assets/ to app/assets/ if needed"
        }
    )


@router.get("/pins", response_model=List[MapPin])
async def get_pins():
    """Get all pinned locations."""
    return load_pins()


@router.post("/pins")
async def save_pins_endpoint(pins: List[MapPin]):
    """Save pinned locations."""
    try:
        save_pins(pins)
        return {"status": "success", "count": len(pins)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save pins: {str(e)}")


@router.get("/routes", response_model=List[FlightRoute])
async def get_routes():
    """Get all flight routes."""
    return load_routes()


@router.post("/routes")
async def save_routes_endpoint(routes: List[FlightRoute]):
    """Save flight routes."""
    try:
        save_routes(routes)
        return {"status": "success", "count": len(routes)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save routes: {str(e)}")


@router.get("/export/typescript")
async def export_typescript_waypoints():
    """Export pins as TypeScript interface for the dynamic background system."""
    pins = load_pins()
    
    if not pins:
        raise HTTPException(status_code=404, detail="No pins found to export")
    
    # Generate TypeScript code
    ts_content = f'''// Generated Map Waypoints for PL8WRDS Dynamic Background
// Generated on {datetime.now().isoformat()}
// Total waypoints: {len(pins)}

interface MapWaypoint {{
  id: string;
  name: string;
  x_percent: number;
  y_percent: number;
  category: 'city' | 'landmark' | 'junction' | 'airport';
}}

export const VINTAGE_MAP_WAYPOINTS: MapWaypoint[] = [
'''
    
    for pin in pins:
        ts_content += f'''  {{
    id: '{pin.id}',
    name: '{pin.name}',
    x_percent: {pin.x_percent:.2f},
    y_percent: {pin.y_percent:.2f},
    category: '{pin.category}'
  }},
'''
    
    ts_content += '''];

// Utility function to get waypoint by name
export function getWaypoint(name: string): MapWaypoint | undefined {
  return VINTAGE_MAP_WAYPOINTS.find(wp => wp.name.toLowerCase() === name.toLowerCase());
}

// Generate CSS keyframe between two waypoints
export function generateFlightPath(from: string, to: string, routeName: string): string {
  const fromWp = getWaypoint(from);
  const toWp = getWaypoint(to);
  
  if (!fromWp || !toWp) {
    throw new Error(`Waypoints not found: ${from} -> ${to}`);
  }
  
  return `@keyframes ${routeName} {
  0% {
    transform: scale(var(--flyover-altitude)) translate(-35%, -3%);
    background-position: ${fromWp.x_percent.toFixed(1)}% ${fromWp.y_percent.toFixed(1)}%;
  }
  100% {
    transform: scale(var(--flyover-altitude)) translate(35%, 2%);
    background-position: ${toWp.x_percent.toFixed(1)}% ${toWp.y_percent.toFixed(1)}%;
  }
}`;
}

// Example flight routes based on your pinned locations
export const SUGGESTED_ROUTES = [
'''
    
    # Generate some example routes if we have enough pins
    if len(pins) >= 2:
        major_cities = [p for p in pins if p.category == 'city'][:4]
        if len(major_cities) >= 2:
            ts_content += f"  // {major_cities[0].name} to {major_cities[1].name} route\n"
            ts_content += f"  generateFlightPath('{major_cities[0].name}', '{major_cities[1].name}', 'route1'),\n"
            if len(major_cities) >= 4:
                ts_content += f"  // {major_cities[2].name} to {major_cities[3].name} route\n"
                ts_content += f"  generateFlightPath('{major_cities[2].name}', '{major_cities[3].name}', 'route2'),\n"
    
    ts_content += '];'
    
    return JSONResponse(
        content={"typescript_code": ts_content},
        headers={
            "Content-Disposition": "attachment; filename=vintage-map-waypoints.ts"
        }
    )


@router.get("/export/css")
async def export_css_animations():
    """Export pins as CSS animations for direct use in backgrounds.css."""
    pins = load_pins()
    
    if not pins:
        raise HTTPException(status_code=404, detail="No pins found to export")
    
    css_content = f'''/* Generated CSS Animations for PL8WRDS Vintage Map
   Generated on {datetime.now().isoformat()}
   Based on {len(pins)} pinned locations */

'''
    
    # Generate realistic flight routes between major cities
    major_cities = [p for p in pins if p.category == 'city']
    
    route_num = 1
    for i, city1 in enumerate(major_cities):
        for j, city2 in enumerate(major_cities[i+1:], i+1):
            css_content += f'''/* Route {route_num}: {city1.name} to {city2.name} */
@keyframes vintageMapRoute{route_num} {{
  0% {{
    transform: scale(var(--flyover-altitude)) translate(-35%, -3%);
    background-position: {city1.x_percent:.1f}% {city1.y_percent:.1f}%;
  }}
  100% {{
    transform: scale(var(--flyover-altitude)) translate(35%, 2%);
    background-position: {city2.x_percent:.1f}% {city2.y_percent:.1f}%;
  }}
}}

'''
            route_num += 1
            if route_num > 10:  # Limit to 10 routes
                break
        if route_num > 10:
            break
    
    return JSONResponse(
        content={"css_code": css_content},
        headers={
            "Content-Disposition": "attachment; filename=vintage-map-routes.css"
        }
    )


@router.delete("/pins")
async def clear_all_pins():
    """Clear all pinned locations."""
    try:
        if PINS_FILE.exists():
            PINS_FILE.unlink()
        if ROUTES_FILE.exists():
            ROUTES_FILE.unlink()
        return {"status": "success", "message": "All pins and routes cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear data: {str(e)}")


@router.get("/status")
async def get_mapping_status():
    """Get status of the map pinning system."""
    pins = load_pins()
    routes = load_routes()
    
    return {
        "pins_count": len(pins),
        "routes_count": len(routes),
        "categories": list(set(pin.category for pin in pins)),
        "data_files_exist": {
            "pins": PINS_FILE.exists(),
            "routes": ROUTES_FILE.exists()
        },
        "ready_for_export": len(pins) >= 2
    }
