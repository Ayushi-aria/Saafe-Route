# SafeRoute: Risk-Aware Vehicle Routing Optimizer 🚑🚦

**SafeRoute** is an intelligent navigation system designed to prioritize safety over speed when necessary. It uses **Google OR-Tools** to solve the Vehicle Routing Problem (VRP) while accounting for dynamic hazards like road blocks, construction, or accidents.

The application features a Python Flask backend for optimization and an interactive Leaflet.js frontend for real-time visualization and hazard simulation.

## 🌟 Features

-   **Risk-Aware Routing**: Calculates routes based on a cost function: $Cost = Distance + (\lambda \times Risk)$.
-   **Dynamic Hazard Simulation**: Click anywhere on the map to "block" a road.
-   **Real-Time Rerouting**: The solver instantly finds the optimal *safe* alternative path, avoiding high-risk zones.
-   **Pareto Analysis**: Includes tools to analyze the trade-off between speed (distance) and safety (risk).
-   **Interactive Map**: Built with Leaflet.js and OpenStreetMap for a seamless user experience.

## 🛠️ Tech Stack

-   **Backend**: Python, Flask
-   **Optimization Engine**: Google OR-Tools (Constraint Solver)
-   **Frontend**: HTML5, CSS3 (Glassmorphism), JavaScript (Vanilla)
-   **Mapping**: Leaflet.js, OpenStreetMap
-   **Data Analysis**: Jupyter Notebook, Matplotlib

## 🚀 Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/Ayushi-aria/Saafe-Route.git
    cd Saafe-Route
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Application**
    ```bash
    python app.py
    ```

4.  **Access the App**
    The app should open automatically in your browser. If not, visit:
    `http://127.0.0.1:5000`

## 📖 How to Use

1.  **View Optimal Path**: On launch, the Green path shows the fastest route visiting all 5 locations in Dhanbad.
2.  **Simulate a Hazard**:
    -   Click the **"Simulate Hazard"** button.
    -   Click anywhere on the map (e.g., on the green route to block it).
3.  **Observe Rerouting**:
    -   The system identifies the blockage.
    -   The path turns **RED**, indicating "Hazard Avoidance Mode".
    -   A new, safe route is calculated and displayed.

## 🧠 Mathematical Logic

The core logic resides in `solver_engine.py`. We use a weighted cost function:

$$
\text{Total Cost} = \text{Distance} + (\lambda \times \text{Risk Score})
$$

-   **Standard Risk**: 0-100 based on road quality/traffic.
-   **Blocked Risk**: >1,000,000 (Soft Constraint penalty turned to Hard Constraint via cost).

## 📂 Project Structure

-   `app.py`: Flask application server.
-   `solver_engine.py`: Core OR-Tools optimization logic.
-   `analysis.ipynb`: Jupyter notebook for Pareto trade-off analysis.
-   `static/`: CSS and JavaScript files.
-   `templates/`: HTML templates.

## 🤝 Contributing

Contributions are welcome! Please fork the repository and submit a pull request.
