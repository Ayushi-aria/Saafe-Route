from flask import Flask, request, jsonify, render_template
import json
from solver_engine import RiskAwareSolver

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/route', methods=['POST'])
def get_route():
    data = request.get_json()
    blocked_coords = data.get('blocked_coordinates', [])
    
    # Instantiate solver
    solver = RiskAwareSolver()
    
    # Solve with default safety weight or user provided
    # Prompt implies we just need to return optimal safe path.
    # We'll use a moderate safety weight (e.g., 5.0) to prioritize safety when blocks appear.
    # Ideally this would be dynamic too, but for prompt 3/4 "Simulate Hazard", 
    # the blocked logic (hard constraint) is handled by the solver's block check.
    result = solver.solve(safety_weight_lambda=5.0, blocked_coords=blocked_coords)
    
    if not result['success']:
        return jsonify({"error": "No solution found"}), 400
        
    # Construct GeoJSON
    features = []
    
    # Route LineString
    route_coords = [[lng, lat] for lat, lng in result['route_coords']] # GeoJSON is [lng, lat]
    features.append({
        "type": "Feature",
        "properties": {"stroke": "red" if blocked_coords else "blue"}, # Visual style
        "geometry": {
            "type": "LineString",
            "coordinates": route_coords
        }
    })
    
    response = {
        "type": "FeatureCollection",
        "features": features,
        "metrics": {
            "safe_distance": result['total_distance'],
            "total_risk": result['total_risk'],
            "nodes_visited": len(result['route_indices'])
        }
    }
    
    return jsonify(response)

if __name__ == '__main__':
    import webbrowser
    import threading
    
    def open_browser():
        webbrowser.open_new('http://127.0.0.1:5000/')
        
    print("Starting SafeRoute Server...")
    print("Your browser should open automatically in a moment.")
    print("If not, please visit http://127.0.0.1:5000 manually.")
    
    # Timer to open browser after a short delay to ensure server is ready
    threading.Timer(1.5, open_browser).start()
    
    app.run(host='0.0.0.0', port=5000, debug=True)
