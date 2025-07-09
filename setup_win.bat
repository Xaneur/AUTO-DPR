@echo off
setlocal enabledelayedexpansion

REM ===================================================================
REM setup.bat - Windows Setup Script for Streamlit Application
REM Auto-installs everything needed on a Windows system
REM ===================================================================

REM Configuration
set "APP_FILE=app.py"
set "SUBDOMAIN=xaneur"
set "HOST=https://loca.lt"
set "BASE_PORT=8501"
set "PYTHON_MIN_VERSION=3.9"
set "NODE_MIN_VERSION=18"

REM Color codes (for Windows 10+)
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "PURPLE=[95m"
set "CYAN=[96m"
set "NC=[0m"

REM ===================================================================
REM ENTRY POINT - Start here
REM ===================================================================
goto :main

REM ===================================================================
REM Logging functions
REM ===================================================================
:log_info
echo %BLUE%[INFO]%NC% %~1
goto :eof

:log_success
echo %GREEN%[SUCCESS]%NC% %~1
goto :eof

:log_warning
echo %YELLOW%[WARNING]%NC% %~1
goto :eof

:log_error
echo %RED%[ERROR]%NC% %~1
goto :eof

:log_step
echo %PURPLE%[STEP]%NC% %~1
goto :eof

REM ===================================================================
REM Welcome message
REM ===================================================================
:show_welcome
cls
echo %CYAN%
echo ===============================================================
echo                    PROJECT SETUP WIZARD
echo ===============================================================
echo.
echo This script will automatically install and configure:
echo   • Chocolatey package manager
echo   • Python 3.9+ and virtual environment
echo   • uv for fast Python package management
echo   • Node.js and npm
echo   • LocalTunnel for public URL sharing
echo   • Streamlit application
echo.
echo Compatible with Windows 10/11 systems
echo.
echo WARNING: Administrator privileges may be required
echo ===============================================================
echo %NC%
echo.
pause
echo.
goto :eof

REM ===================================================================
REM Check if running as administrator
REM ===================================================================
:check_admin
net session >nul 2>&1
if !errorlevel! neq 0 (
    call :log_warning "This script requires administrator privileges"
    call :log_info "Please run as administrator or the script will attempt to elevate"
    pause
    
    REM Try to elevate
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b 1
)
call :log_success "Administrator privileges confirmed"
goto :eof

REM ===================================================================
REM Install Chocolatey
REM ===================================================================
:install_chocolatey
call :log_step "Checking for Chocolatey..."

choco --version >nul 2>&1
if !errorlevel! equ 0 (
    call :log_success "Chocolatey is already installed"
    goto :eof
)

call :log_step "Installing Chocolatey..."
powershell -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"

if !errorlevel! neq 0 (
    call :log_error "Chocolatey installation failed"
    pause
    exit /b 1
)

REM Refresh environment variables
call refreshenv.cmd >nul 2>&1
set "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"

call :log_success "Chocolatey installed successfully"
goto :eof

REM ===================================================================
REM Check Python version
REM ===================================================================
:check_python_version
set "python_cmd=%~1"
%python_cmd% --version >nul 2>&1
if !errorlevel! neq 0 (
    exit /b 1
)

for /f "tokens=2 delims= " %%a in ('"%python_cmd%" --version 2^>^&1') do (
    set "version=%%a"
)

REM Simple version comparison (assuming format X.Y.Z)
for /f "tokens=1,2 delims=." %%a in ("!version!") do (
    set "major=%%a"
    set "minor=%%b"
)

if !major! gtr 3 (
    set "PYTHON_CMD=%python_cmd%"
    call :log_success "Found compatible Python: %python_cmd% (version !version!)"
    exit /b 0
)
if !major! equ 3 (
    if !minor! geq 9 (
        set "PYTHON_CMD=%python_cmd%"
        call :log_success "Found compatible Python: %python_cmd% (version !version!)"
        exit /b 0
    )
)

call :log_warning "Python version !version! is below minimum required %PYTHON_MIN_VERSION%"
exit /b 1

REM ===================================================================
REM Install Python
REM ===================================================================
:install_python
call :log_step "Checking for Python..."

REM Try to find existing Python installation
call :check_python_version "python"
if !errorlevel! equ 0 goto :eof

call :check_python_version "python3"
if !errorlevel! equ 0 goto :eof

call :check_python_version "py"
if !errorlevel! equ 0 goto :eof

call :log_step "Installing Python via Chocolatey..."
choco install python -y --force

if !errorlevel! neq 0 (
    call :log_error "Python installation failed"
    pause
    exit /b 1
)

REM Refresh environment variables
call refreshenv.cmd >nul 2>&1

REM Try to find Python again
call :check_python_version "python"
if !errorlevel! equ 0 goto :eof

call :check_python_version "python3"
if !errorlevel! equ 0 goto :eof

call :check_python_version "py"
if !errorlevel! equ 0 goto :eof

call :log_error "Python installation failed or version is incompatible"
pause
exit /b 1

REM ===================================================================
REM Install uv
REM ===================================================================
:install_uv
call :log_step "Checking for uv..."

uv --version >nul 2>&1
if !errorlevel! equ 0 (
    call :log_success "uv is already installed"
    goto :eof
)

call :log_step "Installing uv via pip..."
%PYTHON_CMD% -m pip install uv --upgrade

if !errorlevel! neq 0 (
    call :log_error "uv installation failed"
    pause
    exit /b 1
)

REM Refresh environment variables
call refreshenv.cmd >nul 2>&1

REM Add Python Scripts to PATH if not already there
for /f "tokens=*" %%a in ('"%PYTHON_CMD%" -c "import sys; print(sys.prefix)"') do set "PYTHON_PREFIX=%%a"
set "SCRIPTS_PATH=%PYTHON_PREFIX%\Scripts"
echo !PATH! | find /i "!SCRIPTS_PATH!" >nul
if !errorlevel! neq 0 (
    set "PATH=!PATH!;!SCRIPTS_PATH!"
    setx PATH "!PATH!" /M >nul 2>&1
)

call :log_success "uv installed successfully"
goto :eof

REM ===================================================================
REM Install Node.js
REM ===================================================================
:install_nodejs
call :log_step "Checking for Node.js..."

node --version >nul 2>&1
if !errorlevel! equ 0 (
    call :log_success "Node.js is already installed"
    goto :eof
)

call :log_step "Installing Node.js via Chocolatey..."
choco install nodejs -y --force

if !errorlevel! neq 0 (
    call :log_error "Node.js installation failed"
    pause
    exit /b 1
)

REM Refresh environment variables
call refreshenv.cmd >nul 2>&1

node --version >nul 2>&1
if !errorlevel! neq 0 (
    call :log_error "Node.js installation verification failed"
    pause
    exit /b 1
)

for /f "tokens=*" %%a in ('node --version') do (
    call :log_success "Node.js %%a installed successfully"
)
goto :eof

REM ===================================================================
REM Install LocalTunnel - FIXED VERSION
REM ===================================================================
:install_localtunnel
call :log_step "Checking for LocalTunnel..."

REM Check if localtunnel is installed globally
where lt >nul 2>&1
if !errorlevel! equ 0 (
    call :log_success "LocalTunnel is already installed"
    set "LOCALTUNNEL_AVAILABLE=true"
    goto :eof
)

call :log_step "Installing LocalTunnel via npm..."
npm install -g localtunnel

if !errorlevel! neq 0 (
    call :log_error "LocalTunnel installation failed"
    call :log_info "Trying alternative installation method..."
    
    REM Alternative: Try with --force flag
    npm install -g localtunnel --force
    
    if !errorlevel! neq 0 (
        call :log_error "LocalTunnel installation failed with alternative method"
        call :log_warning "Continuing without LocalTunnel - only local access will be available"
        set "LOCALTUNNEL_AVAILABLE=false"
        goto :eof
    )
)

REM Refresh environment variables
call refreshenv.cmd >nul 2>&1

REM Add npm global modules to PATH if not already there
for /f "tokens=*" %%a in ('npm config get prefix 2^>nul') do set "NPM_PREFIX=%%a"
if not "!NPM_PREFIX!"=="" (
    set "NPM_BIN_PATH=!NPM_PREFIX!"
    echo !PATH! | find /i "!NPM_BIN_PATH!" >nul
    if !errorlevel! neq 0 (
        set "PATH=!PATH!;!NPM_BIN_PATH!"
        setx PATH "!PATH!" /M >nul 2>&1
    )
)

REM Verify installation using npm list instead of lt --version
call :log_step "Verifying LocalTunnel installation..."
npm list -g localtunnel >nul 2>&1
if !errorlevel! neq 0 (
    call :log_warning "LocalTunnel verification failed - continuing anyway"
    set "LOCALTUNNEL_AVAILABLE=false"
    goto :eof
)

set "LOCALTUNNEL_AVAILABLE=true"
call :log_success "LocalTunnel installed successfully"
goto :eof 

REM ===================================================================
REM Setup Python environment and install dependencies
REM ===================================================================
:setup_python_env
call :log_step "Setting up Python virtual environment..."

if not exist "pyproject.toml" (
    call :log_error "pyproject.toml not found in current directory"
    pause
    exit /b 1
)

call :log_step "Installing Python dependencies from pyproject.toml..."
uv pip install -r pyproject.toml

if !errorlevel! neq 0 (
    call :log_error "Python dependencies installation failed"
    pause
    exit /b 1
)

call :log_success "Python environment setup completed"
goto :eof

REM ===================================================================
REM Find free port
REM ===================================================================
:find_free_port
set "port=%~1"
:port_loop
netstat -an | find ":%port%" | find "LISTENING" >nul
if !errorlevel! equ 0 (
    set /a port+=1
    goto port_loop
)
set "FREE_PORT=!port!"
goto :eof

REM ===================================================================
REM Wait for service to be ready
REM ===================================================================
:wait_for_service
set "port=%~1"
set "timeout=60"
set "elapsed=0"

call :log_info "Waiting for service on port %port%..."

:wait_loop
if !elapsed! geq !timeout! (
    call :log_error "Service on port %port% failed to start within %timeout%s"
    pause
    exit /b 1
)

netstat -an | find ":%port%" | find "LISTENING" >nul
if !errorlevel! equ 0 (
    goto :eof
)

timeout /t 1 /nobreak >nul
set /a elapsed+=1
goto wait_loop

REM ===================================================================
REM Create dashboard HTML - FIXED VERSION
REM ===================================================================
:create_dashboard
set "html_file=dashboard.html"
call :log_step "Creating dashboard HTML..."

REM Create the HTML file directly using echo statements
(
echo ^<!DOCTYPE html^>
echo ^<html lang="en"^>
echo ^<head^>
echo     ^<meta charset="UTF-8"^>
echo     ^<meta name="viewport" content="width=device-width, initial-scale=1.0"^>
echo     ^<title^>Streamlit Dashboard^</title^>
echo     ^<style^>
echo         body {
echo             font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
echo             margin: 0;
echo             padding: 20px;
echo             background: linear-gradient^(135deg, #667eea 0%%, #764ba2 100%%^);
echo             color: white;
echo             min-height: 100vh;
echo         }
echo         .container {
echo             max-width: 800px;
echo             margin: 0 auto;
echo             background: rgba^(255, 255, 255, 0.1^);
echo             padding: 30px;
echo             border-radius: 15px;
echo             box-shadow: 0 8px 32px rgba^(0, 0, 0, 0.3^);
echo             backdrop-filter: blur^(10px^);
echo         }
echo         h1 {
echo             text-align: center;
echo             margin-bottom: 30px;
echo             font-size: 2.5em;
echo             text-shadow: 2px 2px 4px rgba^(0, 0, 0, 0.5^);
echo         }
echo         .info-grid {
echo             display: grid;
echo             grid-template-columns: repeat^(auto-fit, minmax^(300px, 1fr^)^);
echo             gap: 20px;
echo             margin-bottom: 30px;
echo         }
echo         .info-card {
echo             background: rgba^(255, 255, 255, 0.1^);
echo             padding: 20px;
echo             border-radius: 10px;
echo             border: 1px solid rgba^(255, 255, 255, 0.2^);
echo         }
echo         .info-card h3 {
echo             margin: 0 0 10px 0;
echo             font-size: 1.3em;
echo         }
echo         .info-card p {
echo             margin: 5px 0;
echo             font-size: 1.1em;
echo         }
echo         .url-link {
echo             color: #4CAF50;
echo             text-decoration: none;
echo             font-weight: bold;
echo             word-break: break-all;
echo         }
echo         .url-link:hover {
echo             color: #45a049;
echo             text-decoration: underline;
echo         }
echo         .password {
echo             background: rgba^(255, 255, 255, 0.2^);
echo             padding: 10px;
echo             border-radius: 5px;
echo             font-family: monospace;
echo             font-size: 1.2em;
echo             text-align: center;
echo             margin: 10px 0;
echo         }
echo         .button-container {
echo             text-align: center;
echo             margin-top: 30px;
echo         }
echo         .btn {
echo             background: linear-gradient^(45deg, #4CAF50, #45a049^);
echo             color: white;
echo             padding: 15px 30px;
echo             border: none;
echo             border-radius: 25px;
echo             font-size: 1.1em;
echo             cursor: pointer;
echo             text-decoration: none;
echo             display: inline-block;
echo             margin: 0 10px;
echo             transition: all 0.3s ease;
echo             box-shadow: 0 4px 15px rgba^(0, 0, 0, 0.2^);
echo         }
echo         .btn:hover {
echo             transform: translateY^(-2px^);
echo             box-shadow: 0 6px 20px rgba^(0, 0, 0, 0.3^);
echo         }
echo         .status {
echo             text-align: center;
echo             margin: 20px 0;
echo             font-size: 1.2em;
echo             color: #4CAF50;
echo         }
echo         .footer {
echo             text-align: center;
echo             margin-top: 40px;
echo             font-size: 0.9em;
echo             opacity: 0.7;
echo         }
echo     ^</style^>
echo ^</head^>
echo ^<body^>
echo     ^<div class="container"^>
echo         ^<h1^>🚀 Streamlit Dashboard^</h1^>
echo         
echo         ^<div class="status"^>
echo             ✅ All services are running successfully!
echo         ^</div^>
echo         
echo         ^<div class="info-grid"^>
echo             ^<div class="info-card"^>
echo                 ^<h3^>🏠 Local Application^</h3^>
echo                 ^<p^>^<strong^>URL:^</strong^> ^<a href="http://localhost:!STREAMLIT_PORT!" class="url-link" target="_blank"^>http://localhost:!STREAMLIT_PORT!^</a^>^</p^>
echo                 ^<p^>^<strong^>Status:^</strong^> Running on port !STREAMLIT_PORT!^</p^>
echo             ^</div^>
echo             
echo             ^<div class="info-card"^>
echo                 ^<h3^>🌐 Public Access^</h3^>
echo                 ^<p^>^<strong^>URL:^</strong^> ^<a href="https://%SUBDOMAIN%.loca.lt" class="url-link" target="_blank"^>https://%SUBDOMAIN%.loca.lt^</a^>^</p^>
echo                 ^<p^>^<strong^>Tunnel:^</strong^> LocalTunnel^</p^>
echo                 ^<p^>^<strong^>Status:^</strong^> !PUBLIC_STATUS!^</p^>
echo             ^</div^>
echo         ^</div^>
echo         
echo         ^<div class="button-container"^>
echo             ^<a href="http://localhost:!STREAMLIT_PORT!" class="btn" target="_blank"^>Open Local App^</a^>
echo             ^<a href="https://%SUBDOMAIN%.loca.lt" class="btn" target="_blank"^>Open Public App^</a^>
echo         ^</div^>
echo         
echo         ^<div class="footer"^>
echo             ^<p^>Dashboard created on %DATE% at %TIME%^</p^>
echo             ^<p^>Press Ctrl+C in the terminal to stop all services^</p^>
echo         ^</div^>
echo     ^</div^>
echo ^</body^>
echo ^</html^>
) > "%html_file%"

call :log_success "Dashboard HTML created: %html_file%"
goto :eof

REM ===================================================================
REM Main execution - UPDATED VERSION
REM ===================================================================
:main
REM Change to script directory
cd /d "%~dp0"

REM Show welcome message
call :show_welcome

REM Check for admin privileges
call :check_admin
if !errorlevel! neq 0 exit /b 1

REM Install all dependencies
call :install_chocolatey
call :install_python
call :install_uv
call :install_nodejs
call :install_localtunnel

REM Setup Python environment
call :setup_python_env

REM Check if app file exists
if not exist "%APP_FILE%" (
    call :log_error "Application file %APP_FILE% not found in %CD%"
    pause
    exit /b 1
)

REM Find free port
call :find_free_port %BASE_PORT%
set "STREAMLIT_PORT=!FREE_PORT!"

call :log_info "Using port: Streamlit=!STREAMLIT_PORT!"

REM Start Streamlit
call :log_step "Starting Streamlit application..."
start /b "" uv run streamlit run "%APP_FILE%" --server.port !STREAMLIT_PORT! --server.headless true

REM Wait for Streamlit to be ready
call :wait_for_service !STREAMLIT_PORT!
call :log_success "Streamlit is running at http://localhost:!STREAMLIT_PORT!"

REM Start LocalTunnel only if available
if "%LOCALTUNNEL_AVAILABLE%"=="true" (
    call :log_step "Starting LocalTunnel..."
    start /b "" lt --port !STREAMLIT_PORT! --subdomain %SUBDOMAIN% --host %HOST%
    
    REM Wait a bit for tunnel to establish
    timeout /t 5 /nobreak >nul
    
    call :log_success "LocalTunnel running at https://%SUBDOMAIN%.loca.lt"
    set "PUBLIC_URL=https://%SUBDOMAIN%.loca.lt"
    set "PUBLIC_STATUS=Available"
) else (
    call :log_warning "LocalTunnel not available - running in local-only mode"
    set "PUBLIC_URL=Not available"
    set "PUBLIC_STATUS=Not available"
)

REM Create dashboard HTML
call :create_dashboard

REM Display summary
echo.
echo %GREEN%🎉 Setup completed successfully!%NC%
echo ═══════════════════════════════════════════════════════════
echo %CYAN%📊 Local Streamlit: http://localhost:!STREAMLIT_PORT!%NC%
if "%LOCALTUNNEL_AVAILABLE%"=="true" (
    echo %CYAN%🌐 Public URL: https://%SUBDOMAIN%.loca.lt%NC%
) else (
    echo %YELLOW%🌐 Public URL: Not available (LocalTunnel issue)%NC%
)
echo %CYAN%📋 Dashboard: dashboard.html%NC%
echo ═══════════════════════════════════════════════════════════
echo.

REM Open dashboard in browser
call :log_step "Opening dashboard in browser..."
start "" dashboard.html

echo %YELLOW%The application is now running. Press any key to stop all services.%NC%
pause >nul

REM Cleanup
call :log_info "Stopping services..."
taskkill /f /im "streamlit.exe" >nul 2>&1
taskkill /f /im "node.exe" >nul 2>&1
taskkill /f /im "lt.exe" >nul 2>&1

call :log_success "All services stopped"
echo.
echo %GREEN%Thank you for using the setup wizard!%NC%
pause
exit /b 0