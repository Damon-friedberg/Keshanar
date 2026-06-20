# One-shot local setup for JARVIS. Run from the jarvis\ folder in PowerShell:
#   .\setup.ps1
$ErrorActionPreference = "Stop"

Write-Host "== JARVIS local setup ==" -ForegroundColor Cyan

if (-not (Test-Path .venv)) {
  Write-Host "Creating virtual env (.venv)..."
  py -m venv .venv
}
. .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip | Out-Null
Write-Host "Installing core (text mode)..."
pip install -e .

if (-not (Test-Path .env)) {
  Copy-Item .env.example .env
  Write-Host "Created .env from template." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Green
Write-Host "  1) Edit .env  ->  ANTHROPIC_API_KEY,  JARVIS_MODEL_FAST=claude-sonnet-4-6,  JARVIS_MODEL_HEAVY=claude-opus-4-8"
Write-Host "  2) py -m jarvis.doctor --ping        (verify keys + a live model call)"
Write-Host "  3) py -m jarvis.chat                 (talk to it in text)"
Write-Host ""
Write-Host "For voice + orb later:  pip install -e `".[voice,capture,hud]`"  then  py -m jarvis.main"
