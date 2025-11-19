#!/usr/bin/env pwsh
<#
Creates a local .venv, activates it in the current session, upgrades pip,
and installs dependencies from requirements.txt.

Usage (run from project root):
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  .\scripts\setup_venv.ps1
#>

param(
    [string]$VenvPath = '.venv',
    [string]$Requirements = 'requirements.txt'
)

Write-Host "Creating virtual environment at $VenvPath" -ForegroundColor Cyan
# Try to create the venv and surface errors if it fails
Write-Host "Invoking: python -m venv $VenvPath" -ForegroundColor Cyan
try {
    $proc = Start-Process -FilePath (Get-Command python).Source -ArgumentList '-m','venv',$VenvPath -NoNewWindow -Wait -PassThru -ErrorAction Stop
    if ($proc.ExitCode -ne 0) {
        Write-Error "Virtual environment creation failed with exit code $($proc.ExitCode)."
        Write-Host 'Dumping recent errors:' -ForegroundColor Yellow
        $error[0..5] | ForEach-Object { Write-Host $_ }
        exit 1
    }
} catch {
    Write-Error "Failed to create virtual environment: $_"
    Write-Host 'If this error is about permissions or Python, try running this manually to see full output:' -ForegroundColor Yellow
    Write-Host "  python -m venv $VenvPath"
    exit 1
}

# Activate the venv in the current session
$activate = Join-Path $VenvPath 'Scripts/Activate.ps1'
if (Test-Path $activate) {
    Write-Host "Activating virtual environment..." -ForegroundColor Cyan
    . $activate
}
else {
    Write-Error "Activation script not found at $activate"
    exit 1
}

Write-Host "Upgrading pip and installing requirements..." -ForegroundColor Cyan
python -m pip install --upgrade pip
if (Test-Path $Requirements) {
    pip install -r $Requirements
}
else {
    Write-Warning "$Requirements not found. Skipping dependency install."
}

Write-Host "Setup complete. Virtual environment is active in this session." -ForegroundColor Green
