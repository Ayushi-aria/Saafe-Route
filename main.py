from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def create_data_model():
    """Stores the data for the problem."""
    data = {}
    # Locations: 0: ISM, 1: Station, 2: City Centre, 3: Hirapur, 4: Bank More
    # Distances in meters (approximate/dummy for demo)
    data['distance_matrix'] = [
        [0, 3000, 4000, 2000, 5000],  # 0: ISM
        [3000, 0, 1500, 3500, 2000],  # 1: Station
        [4000, 1500, 0, 2500, 1000],  # 2: City Centre (Target blocked from 0)
        [2000, 3500, 2500, 0, 4000],  # 3: Hirapur
        [5000, 2000, 1000, 4000, 0],  # 4: Bank More
    ]
    data['num_vehicles'] = 1
    data['depot'] = 0
    return data

def print_solution(manager, routing, solution):
    """Prints solution on console."""
    print(f'Objective: {solution.ObjectiveValue()}')
    index = routing.Start(0)
    plan_output = 'Route for vehicle 0:\n'
    route_distance = 0
    while not routing.IsEnd(index):
        plan_output += f' {manager.IndexToNode(index)} ->'
        previous_index = index
        index = solution.Value(routing.NextVar(index))
        route_distance += routing.GetArcCostForVehicle(previous_index, index, 0)
    plan_output += f' {manager.IndexToNode(index)}\n'
    plan_output += f'Distance of the route: {route_distance}m\n'
    print(plan_output)

def main():
    """Entry point of the program."""
    # Instantiate the data problem.
    data = create_data_model()
    
    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']),
                                           data['num_vehicles'], data['depot'])

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

    # 1. basic distance callback
    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    
    # 2. Add Risk/Penalty Callback
    # Scenario: Road from 0 (ISM) to 2 (City Centre) is blocked/high risk.
    # We add a huge penalty to this specific arc.
    
    BLOCKED_PENALTY = 100000 # Very high cost to avoid this path
    
    def risk_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        
        # Check for the blocked road: 0 -> 2
        # Note: In VRP usually we set arc costs. Here we combine distance + penalty.
        cost = data['distance_matrix'][from_node][to_node]
        
        if from_node == 0 and to_node == 2:
            print(f"DEBUG: Applying penalty for blocked road {from_node} -> {to_node}")
            cost += BLOCKED_PENALTY
            
        return cost

    risk_callback_index = routing.RegisterTransitCallback(risk_callback)

    # Define cost of each arc.
    # We use the risk_callback_index for the arc costs so the solver sees the penalties.
    routing.SetArcCostEvaluatorOfAllVehicles(risk_callback_index)

    # Setting parameters
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    # Print solution on console.
    if solution:
        print_solution(manager, routing, solution)
        
        # Verify if blocked road was used
        route_nodes = []
        index = routing.Start(0)
        while not routing.IsEnd(index):
            route_nodes.append(manager.IndexToNode(index))
            index = solution.Value(routing.NextVar(index))
        route_nodes.append(manager.IndexToNode(index))
        
        print("\nVerification:")
        # blocked is 0 -> 2. Check if (0, 2) sequence exists.
        blocked_used = False
        for i in range(len(route_nodes)-1):
            if route_nodes[i] == 0 and route_nodes[i+1] == 2:
                blocked_used = True
                break
        
        if blocked_used:
             print("FAILURE: The solver used the blocked road (0 -> 2)!")
        else:
             print("SUCCESS: The solver avoided the blocked road (0 -> 2).")

    else:
        print('No solution found!')

if __name__ == '__main__':
    main()
