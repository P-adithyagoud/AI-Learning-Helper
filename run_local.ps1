# AI Learning Planner - Local Launch Script

# 1. Start Flask Backend
Write-Host "🚀 Starting Flask Backend on http://localhost:8000..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python main.py"

# 2. Wait for backend to initialize
Start-Sleep -Seconds 2

# 3. Start React Frontend
Write-Host "⚡ Starting Vite Frontend on http://localhost:5173..." -ForegroundColor Gold
Set-Location frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm run dev"

Write-Host "🎉 Both processes started! Check the new terminal windows for logs." -ForegroundColor Green
Write-Host "🌐 Backend: http://localhost:8000"
Write-Host "🌐 Frontend: http://localhost:5173"
