# Backend Server Startup Script (FIXED)
# This script starts the FastAPI backend server correctly

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "  Starting Backend API Server" -ForegroundColor Cyan  
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Server will be available at:" -ForegroundColor Green
Write-Host "  - API: http://localhost:8000" -ForegroundColor Yellow
Write-Host "  - Docs: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "  - Health: http://localhost:8000/health" -ForegroundColor Yellow
Write-Host ""

# Start the server (using main:app from backend directory)
python -c "import uvicorn; uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)"
