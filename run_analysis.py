import matplotlib.pyplot as plt
import numpy as np
from solver_engine import RiskAwareSolver

def run_analysis():
    print("Starting Pareto Analysis...")
    solver = RiskAwareSolver()
    
    lambdas = np.linspace(0, 10, 20)
    distances = []
    risks = []
    
    print(f"Testing Lambdas: {lambdas}")
    
    for lam in lambdas:
        result = solver.solve(safety_weight_lambda=lam)
        if result['success']:
            distances.append(result['total_distance'])
            risks.append(result['total_risk'])
            print(f"Lambda={lam:.2f}: Dist={result['total_distance']}, Risk={result['total_risk']}")
        else:
            print(f"Lambda={lam:.2f}: No Solution")
            distances.append(None)
            risks.append(None)

    # Plotting
    plt.figure(figsize=(10, 6))
    plt.scatter(risks, distances, c=lambdas, cmap='viridis', s=100, edgecolors='black')
    plt.colorbar(label='Safety Weight ($\lambda$)')
    plt.xlabel('Total Risk Score')
    plt.ylabel('Total Distance (m)')
    plt.title('Pareto Frontier: Speed vs. Safety Trade-off')
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Annotate a few points
    for i, lam in enumerate(lambdas):
        if i % 4 == 0 and distances[i] is not None:
            plt.annotate(f'$\lambda={lam:.1f}$', (risks[i], distances[i]), 
                         xytext=(5, 5), textcoords='offset points')
    
    output_file = 'pareto_frontier.png'
    plt.savefig(output_file)
    print(f"Analysis complete. Plot saved to {output_file}")

if __name__ == "__main__":
    run_analysis()
