@echo off
echo ========================================
echo    Snap3D - 启动中...
echo ========================================
echo.
python -m streamlit run app.py --server.headless true --server.port 8585
pause
