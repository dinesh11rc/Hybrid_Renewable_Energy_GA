# Manual Run Specification & Guide

This document provides step-by-step instructions to manually run the **Hybrid Renewable Energy Management System**.

## Prerequisites

Ensure you have the following installed on your system:
- **Python 3.8+**: [Download Here](https://www.python.org/downloads/)
- **Git**: [Download Here](https://git-scm.com/downloads) (Optional, for cloning)

## Project Structure

```
Hybrid_Energy-GA/
├── Backend/               # Python Flask API & Logic
│   ├── server.py          # Main entry point
│   ├── requirements.txt   # Python dependencies
│   └── ...
├── Frontend/              # HTML/JS Dashboard
│   ├── index.html         # Main dashboard interface
│   └── ...
└── ...
```

## Step 1: Backend Setup (Python)

The backend handles data processing, optimization, and API requests.

1.  **Open a terminal/command prompt** and navigate to the project folder:
    ```cmd
    cd d:\Dinesh\Hybrid_Energy-GA
    ```

2.  **Create a Virtual Environment** (Recommended):
    ```cmd
    python -m venv .venv
    ```

3.  **Activate the Virtual Environment**:
    - **Windows**:
      ```cmd
      .venv\Scripts\activate
      ```
    - **Mac/Linux**:
      ```bash
      source .venv/bin/activate
      ```

4.  **Install Dependencies**:
    Navigate to the `Backend` directory and install the required packages:
    ```cmd
    cd Backend
    pip install -r requirements.txt
    ```

5.  **Start the Backend Server**:
    ```cmd
    python server.py
    ```
    You should see output indicating the server is running on `http://127.0.0.1:5000`.

## Step 2: Live Data Simulator

The system uses a simulator to emulate hardware adapters fetching data from solar and wind controllers in real-time.

1.  **Open a new terminal/command prompt** (keep the backend running).
2.  Navigate to the project root and start the simulator:
    ```cmd
    cd d:\Dinesh\Hybrid_Energy-GA
    .venv\Scripts\activate
    python live_data_simulator.py
    ```
    This will push live data every 10 seconds.

## Step 3: Frontend Setup (Web Dashboard)

The frontend is a static web application that connects to the backend.

1.  **Open a new terminal window** (keep the backend running).

2.  **Navigate to the Frontend directory**:
    ```cmd
    cd d:\Dinesh\Hybrid_Energy-GA\Frontend
    ```

3.  **Launch the Dashboard**:
    You can simply open `index.html` in your browser, or start a simple local server for better performance:

    - **Option A (Simple)**: Double-click `index.html` to open it in your browser.
    
    - **Option B (Python Server)**:
      ```cmd
      python -m http.server 8000
      ```
      Then open [http://localhost:8000](http://localhost:8000) in your browser.

## Troubleshooting

-   **"Python was not found"**: Ensure Python is added to your system PATH during installation.
-   **Dependencies fail**: Try upgrading pip: `python -m pip install --upgrade pip`
-   **Port in use**: If port 5000 is busy, edit `server.py` to use a different port (e.g., 5001).

## API Documentation

Once the server is running, you can access the API at `http://localhost:5000`. Functional endpoints include:
-   `POST /optimize`: Run the genetic algorithm.
-   `GET /forecast`: Get energy forecasts.
-   `GET /analytics`: Retrieve historical data.
