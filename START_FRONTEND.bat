@echo off
echo ====================================
echo  MedicSync Frontend - Quick Start
echo ====================================
echo.

cd frontend\streamlit_app
echo [1/2] Activating virtual environment...
call ..\venv\Scripts\activate.bat

echo [2/2] Starting Streamlit server...
echo.
echo Frontend will be available at: http://localhost:8501
echo Backend should be running at: http://localhost:8000
echo.
echo Press CTRL+C to stop the server
echo.

streamlit run app.py
