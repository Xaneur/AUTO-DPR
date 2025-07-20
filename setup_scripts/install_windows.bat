@echo off
SETLOCAL EnableDelayedExpansion

echo Setting up your Windows environment...

:: Check if Chocolatey is installed
where choco >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Installing Chocolatey...
    @powershell -NoProfile -ExecutionPolicy Bypass -Command ^
     "Set-ExecutionPolicy Bypass -Scope Process -Force; ^
     [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; ^
     iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))"
) else (
    echo Chocolatey is already installed.
)

:: Refresh environment variables
refreshenv

:: Install ngrok if not already installed
where ngrok >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Installing ngrok...
    choco install ngrok -y
) else (
    echo ngrok is already installed.
)

echo Setup complete!
pause
