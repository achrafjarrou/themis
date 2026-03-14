Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   THEMIS -- AI Compliance Intelligence " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$BASE = "E:\Dev\projects\themis"
$VENV = "$BASE\.venv\Scripts"

foreach ($port in @(8000, 5173)) {
    $proc = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -ErrorAction SilentlyContinue
    if ($proc) { Stop-Process -Id $proc -Force -ErrorAction SilentlyContinue }
}

Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$BASE'; & '$VENV\Activate.ps1'; uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload`""
Start-Sleep -Seconds 4

$UI = "$BASE\themis-ui"
if (-not (Test-Path $UI)) { $UI = "$BASE\frontend" }
Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$UI'; npm run dev`""

Start-Sleep -Seconds 2
Write-Host "Backend  : http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Frontend : http://localhost:5173"      -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
