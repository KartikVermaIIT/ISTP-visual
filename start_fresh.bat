@echo off
echo ====================================
echo Tree Species Classification WebUI
echo ====================================
echo.
echo Clearing cache and starting fresh...
echo.

REM Clear cache
python clear_cache.py

echo.
echo Starting Streamlit...
echo.
echo The app will open at: http://localhost:8501
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start Streamlit
streamlit run streamlit_app.py
