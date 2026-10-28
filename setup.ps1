# Automated Setup Script for Windows PowerShell
# Usage (from the project folder):  powershell -ExecutionPolicy Bypass -File setup.ps1
Write-Host "Setting up KCK SERVICES..." -ForegroundColor Cyan
$root = $PSScriptRoot

# 1. Setup Backend Virtual Environment
$backend = Join-Path $root "backend"
$backendVenv = Join-Path $backend ".venv"
$backendPython = Join-Path $backendVenv "Scripts\python.exe"
$requirements = Join-Path $backend "requirements.txt"
if (!(Test-Path (Join-Path $backend ".env"))) {
    Copy-Item (Join-Path $backend ".env.example") (Join-Path $backend ".env")
    Write-Host "Created backend/.env from template. Please update it with your Supabase keys!" -ForegroundColor Yellow
}
python -m venv $backendVenv
if ($LASTEXITCODE -ne 0) {
    throw "Failed to create the backend virtual environment."
}
& $backendPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    throw "Failed to upgrade pip in the backend virtual environment."
}
& $backendPython -m pip install -r $requirements
if ($LASTEXITCODE -ne 0) {
    throw "Failed to install backend requirements."
}

# 2. Setup Frontend Node modules
$frontend = Join-Path $root "frontend"
if (!(Test-Path (Join-Path $frontend ".env"))) {
    Copy-Item (Join-Path $frontend ".env.example") (Join-Path $frontend ".env")
    Write-Host "Created frontend/.env from template. Please update it with your Supabase URL & anon key!" -ForegroundColor Yellow
}
npm --prefix $frontend install
if ($LASTEXITCODE -ne 0) {
    throw "Failed to install frontend dependencies."
}

Write-Host "KCK SERVICES Setup Completed!" -ForegroundColor Green
Write-Host "Run the backend:  cd backend; .\.venv\Scripts\Activate.ps1; uvicorn main:app --reload --port 8000"
Write-Host "Swagger UI:       http://localhost:8000/docs"
Write-Host "Run the frontend: cd frontend; npm run dev   ->  http://localhost:5173"
