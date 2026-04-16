@echo off
echo ==========================================================
echo Starting Adaptive Hybrid Renewable Energy Optimization Platform
echo ==========================================================

echo Starting Backend Server...
start cmd /k "cd Backend && pip install -r requirements.txt && python server.py"

echo Starting Frontend Server...
start cmd /k "cd Frontend && python -m http.server 8000"

echo Wait for servers to initialize...
timeout /t 5 >nul

echo Opening browser...
start http://localhost:8000

echo Done! Leave the two terminal windows open.
