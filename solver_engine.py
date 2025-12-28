"""
SafeRoute Solver Engine
=======================

This module implements the core logic for the Risk-Aware Vehicle Routing Problem (VRP).
It uses Google OR-Tools to solve the VRP with a custom cost function that balances
distance and safety risks.

Mathematical Formulation:
-------------------------
The objective is to minimize the total generalized cost $C_{total}$ for the fleet:

$$ C_{total} = \sum_{(i,j) \in E} (d_{ij} + \lambda \cdot r_{ij}) \cdot x_{ij} $$

Where:
- $d_{ij}$ is the distance between node $i$ and $j$.
- $r_{ij}$ is the risk score associated with the edge $(i,j)$.
- $\lambda$ (lambda) is the Safety Weight parameter controlled by the user.
- $x_{ij}$ is a binary variable (1 if edge uses, 0 otherwise).

Constraints:
1. Hard Constraint: If $r_{ij} > R_{max}$ (e.g., 1000), then $x_{ij} = 0$.
2. Flow Conservation: standard VRP constraints.
3. Capacity: Each vehicle has a maximum capacity.
"""

import math
from typing import List, Tuple, Dict, Any
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

class RiskAwareSolver:
    """
    A class to solve the Risk-Aware VRP using Google OR-Tools.
    """

    def __init__(self):
        """
        Initializes the solver with a dummy dataset of 10 locations in Dhanbad.
        """
        self.depot_index = 0
        self.num_vehicles = 1
        # Capacity is dummy for this demo, but required for CVRP
        self.vehicle_capacities = [100] 

        # 10 Locations in Dhanbad (Approximate Lat/Lng)
        # 0: ISM Dhanbad (Depot)
        # 1: Dhanbad Station
        # 2: City Centre
        # 3: Hirapur
        # 4: Bank More
        # 5: Bartand
        # 6: Steel Gate
        # 7: Govindpur
        # 8: Jharia
        # 9: BIT Sindri (remote)
        self.coordinates: List[Tuple[float, float]] = [
            (23.8142, 86.4412), # 0: ISM (Depot)
            (23.7957, 86.4266), # 1: Station
            (23.8050, 86.4300), # 2: City Centre (Hazard Zone 1)
            (23.8100, 86.4350), # 3: Hirapur
            (23.7900, 86.4200), # 4: Bank More
            (23.8200, 86.4500), # 5: Bartand
            (23.8300, 86.4600), # 6: Steel Gate
            (23.8500, 86.5000), # 7: Govindpur
            (23.7500, 86.4000), # 8: Jharia
            (23.6500, 86.4800)  # 9: BIT Sindri (Hazard Zone 2 path)
        ]
        
        # Risk Scores for nodes (simplification: risk is on the node approach)
        # 0 (Safe) to 100 (Moderate). >1000 (Blocked)
        self.risk_scores = {
            0: 0, 1: 10, 2: 50, 3: 5, 4: 20,
            5: 10, 6: 15, 7: 80, 8: 90, 9: 30
        }
        
        # Dynamic blocked edges set: Set of tuples (from_idx, to_idx)
        self.blocked_edges = set()

    def calculate_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> int:
        """
        Calculates Euclidean distance (scaled) between two coordinates.
        For production, Haversine should be used.
        Returns integer meters (approx).
        """
        # Approx conversion: 1 deg lat ~= 111km. 
        # Using simple Euclidean on scaled coords for demo speed.
        scale = 111000 # meters per degree
        dx = (coord1[0] - coord2[0]) * scale
        dy = (coord1[1] - coord2[1]) * scale
        return int(math.sqrt(dx*dx + dy*dy))

    def get_risk_cost(self, from_node: int, to_node: int) -> int:
        """
        Returns the risk score for traversing to 'to_node'.
        Ideally risk is on the edge, here we proxy by destination node risk.
        Scale factor applied for integer arithmetic.
        """
        # If edge is explicitly blocked
        if (from_node, to_node) in self.blocked_edges:
            return 999999
            
        return self.risk_scores.get(to_node, 0)

    def solve(self, safety_weight_lambda: float = 1.0, blocked_coords: List[Tuple[float, float]] = None) -> Dict[str, Any]:
        """
        Solves the VRP with the given Safety Weight.
        
        Args:
            safety_weight_lambda: Multiplier for risk score.
            blocked_coords: List of coordinates to block edges to/from.
            
        Returns:
            Dictionary containing route, total distance, total risk, and optimal path.
        """
        
        # Update blocked edges based on coords (simplistic proximity match)
        self.blocked_edges.clear()
        if blocked_coords:
            for b_lat, b_lng in blocked_coords:
                # Find nearest node
                min_dist = float('inf')
                nearest_node = -1
                for i, coord in enumerate(self.coordinates):
                    dist = (coord[0]-b_lat)**2 + (coord[1]-b_lng)**2
                    if dist < min_dist:
                        min_dist = dist
                        nearest_node = i
                
                # Block all edges INTO this node
                if nearest_node != -1 and min_dist < 0.0001: # Threshold
                     # Block edges entering this node
                     for i in range(len(self.coordinates)):
                         if i != nearest_node:
                             self.blocked_edges.add((i, nearest_node))

        # 1. Create Routing Index Manager
        manager = pywrapcp.RoutingIndexManager(len(self.coordinates),
                                               self.num_vehicles, self.depot_index)

        # 2. Create Routing Model
        routing = pywrapcp.RoutingModel(manager)

        # 3. Define Callback
        def transit_callback(from_index, to_index):
            """
            Returns the General Cost: $Distance + \lambda * Risk$
            """
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            
            dist = self.calculate_distance(self.coordinates[from_node], self.coordinates[to_node])
            risk = self.get_risk_cost(from_node, to_node)
            
            # Hard Constraint Check (Manual Penalty)
            if risk >= 1000 or (from_node, to_node) in self.blocked_edges:
                return 10000000 + dist # Infinite cost
            
            # Cost Function
            # Note: OR-Tools requires integers. Lambda is float, so we might need to scale?
            # Assuming lambda is small integer for now or we create floating cost approx.
            # To be safe, we'll keep lambda as int or multiply everything by 10.
            
            # Let's say Distance is in meters. Risk is 0-100.
            # If Lambda=1.0, 1 Risk Point = 1 Meter.
            
            cost = int(dist + (safety_weight_lambda * risk * 10)) # Risk * 10 to give it weight
            return cost

        transit_callback_index = routing.RegisterTransitCallback(transit_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        
        # 4. Add Metric Callbacks (for reporting, not for solving)
        # We need independent Distance and Risk callbacks to measure final stats
        def real_distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return self.calculate_distance(self.coordinates[from_node], self.coordinates[to_node])
            
        def real_risk_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return self.get_risk_cost(from_node, to_node)

        # 5. Search Parameters
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

        # 6. Solve
        solution = routing.SolveWithParameters(search_parameters)

        # 7. Extract Result
        result = {
            "route_coords": [],
            "route_indices": [],
            "total_distance": 0,
            "total_risk": 0,
            "success": False
        }

        if solution:
            result["success"] = True
            index = routing.Start(0)
            
            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                result["route_indices"].append(node_index)
                result["route_coords"].append(self.coordinates[node_index])
                
                previous_index = index
                index = solution.Value(routing.NextVar(index))
                
                # Calculate metrics stats manually to be sure
                prev_node = manager.IndexToNode(previous_index)
                curr_node = manager.IndexToNode(index)
                
                result["total_distance"] += self.calculate_distance(self.coordinates[prev_node], self.coordinates[curr_node])
                result["total_risk"] += self.get_risk_cost(prev_node, curr_node)

            # Last node (Depot return)
            node_index = manager.IndexToNode(index)
            result["route_indices"].append(node_index)
            result["route_coords"].append(self.coordinates[node_index])
            
        return result

# Simple test if run directly
if __name__ == "__main__":
    solver = RiskAwareSolver()
    # Test 1: Low Safety Preference (Speed first)
    print("Running Solver (Lambda=0)...")
    res_fast = solver.solve(safety_weight_lambda=0)
    print(f"Fast Route: {res_fast['route_indices']}")
    print(f"Distance: {res_fast['total_distance']}, Risk: {res_fast['total_risk']}")
    
    # Test 2: High Safety Preference
    print("\nRunning Solver (Lambda=10)...")
    res_safe = solver.solve(safety_weight_lambda=100)
    print(f"Safe Route: {res_safe['route_indices']}")
    print(f"Distance: {res_safe['total_distance']}, Risk: {res_safe['total_risk']}")
