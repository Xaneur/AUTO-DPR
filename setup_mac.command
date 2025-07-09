#!/bin/bash

# Simple setup script for DPR project
# Just double-click this file to run it

# Open a new Terminal window and run the setup
osascript -e 'tell application "Terminal" to do script "cd \"'$(pwd)'\" && chmod +x setup_simple.command && ./setup_simple.command"'
set -eu
set -o pipefail 2>/dev/null || true  # pipefail might not be available in older bash

# ── Configuration ──────────────────────────────────────────────────────────
APP_FILE="./app.py"
SUBDOMAIN="xaneur"
HOST="https://loca.lt"
BASE_PORT=8501
UI_PORT=7860
PYTHON_MIN_VERSION="3.9"
NODE_MIN_VERSION="18"
RETRY_ATTEMPTS=3
TIMEOUT_SECONDS=60

# ── Color codes for better output ──────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ── Logging functions ──────────────────────────────────────────────────────
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_step() { echo -e "${PURPLE}🔧 $1${NC}"; }

# ── Sudo management ────────────────────────────────────────────────────────
request_sudo_upfront() {
    log_step "Requesting administrator privileges..."
    
    # Check if we need sudo for this system
    local needs_sudo=false
    
    # Check if we're on a system that typically needs sudo
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        needs_sudo=true
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS might need sudo for some operations
        if ! command -v brew &>/dev/null; then
            needs_sudo=true
        fi
    fi
    
    if [ "$needs_sudo" = true ]; then
        echo -e "${YELLOW}This script needs administrator privileges to install system packages.${NC}"
        echo -e "${YELLOW}Please enter your password when prompted.${NC}"
        echo
        
        # Request sudo password upfront
        if ! sudo -v; then
            error_exit "Administrator privileges are required to continue."
        fi
        
        # Keep sudo alive in background
        keep_sudo_alive &
        SUDO_PID=$!
        
        log_success "Administrator privileges granted"
        echo
    else
        log_info "No administrator privileges needed for this system"
    fi
}

# Function to keep sudo alive
keep_sudo_alive() {
    while true; do
        sleep 50
        sudo -v
    done 2>/dev/null
}

# Function to stop sudo keep-alive
stop_sudo_keepalive() {
    if [ -n "${SUDO_PID:-}" ]; then
        kill "$SUDO_PID" 2>/dev/null || true
        unset SUDO_PID
    fi
}

# ── Welcome message ────────────────────────────────────────────────────────
show_welcome() {
    clear
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║                    🚀 PROJECT SETUP WIZARD                       ║"
    echo "║                                                                  ║"
    echo "║  This script will automatically install and configure:           ║"
    echo "║  • Python 3.9+ and virtual environment                           ║"
    echo "║  • Node.js and npm via nvm                                       ║"
    echo "║  • FFmpeg for media processing                                   ║"
    echo "║  • uv for fast Python package management                         ║"
    echo "║  • LocalTunnel for public URL sharing                            ║"
    echo "║  • Streamlit application                                         ║"
    echo "║                                                                  ║"
    echo "║  Compatible with fresh macOS and Linux systems                   ║"
    echo "║                                                                  ║"
    echo "║  ⚠️  Administrator privileges may be required                     ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo
    
    read -p "Press Enter to continue or Ctrl+C to cancel..."
    echo
}

# ── Error handling ─────────────────────────────────────────────────────────
error_exit() {
    log_error "$1"
    echo
    log_error "Setup failed! Check the error message above."
    echo -e "${YELLOW}Press Enter to close this window...${NC}"
    read -r
    cleanup
    exit 1
}

# ── Retry mechanism ────────────────────────────────────────────────────────
retry_command() {
    local command="$1"
    local description="$2"
    local attempt=1
    
    while [ $attempt -le $RETRY_ATTEMPTS ]; do
        log_info "Attempting $description (attempt $attempt/$RETRY_ATTEMPTS)"
        if eval "$command"; then
            return 0
        fi
        log_warning "$description failed on attempt $attempt"
        ((attempt++))
        sleep 2
    done
    
    error_exit "$description failed after $RETRY_ATTEMPTS attempts"
}

# ── System detection ───────────────────────────────────────────────────────
detect_system() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/debian_version ]; then
            DISTRO="debian"
            PKG_MANAGER="apt"
        elif [ -f /etc/redhat-release ]; then
            DISTRO="redhat"
            PKG_MANAGER="yum"
        elif [ -f /etc/arch-release ]; then
            DISTRO="arch"
            PKG_MANAGER="pacman"
        else
            DISTRO="unknown"
            PKG_MANAGER="unknown"
        fi
        OS="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        PKG_MANAGER="brew"
    else
        error_exit "Unsupported operating system: $OSTYPE"
    fi
    
    log_info "Detected system: $OS${DISTRO:+ ($DISTRO)}"
}

# ── Check Python version ───────────────────────────────────────────────────
check_python_version() {
    local python_cmd="$1"
    if ! command -v "$python_cmd" &>/dev/null; then
        return 1
    fi
    
    local version
    version=$($python_cmd --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
    
    if [ "$(printf '%s\n' "$PYTHON_MIN_VERSION" "$version" | sort -V | head -n1)" = "$PYTHON_MIN_VERSION" ]; then
        PYTHON_CMD="$python_cmd"
        log_success "Found compatible Python: $python_cmd (version $version)"
        return 0
    else
        log_warning "Python version $version is below minimum required $PYTHON_MIN_VERSION"
        return 1
    fi
}

# ── Install system dependencies ────────────────────────────────────────────
install_system_deps() {
    log_step "Installing system dependencies..."
    
    # Check for netcat (nc) command
    if ! command -v nc &>/dev/null; then
        log_warning "netcat (nc) not found - installing..."
        case "$OS" in
            "macos")
                # nc is usually pre-installed on macOS
                if ! command -v nc &>/dev/null; then
                    if command -v brew &>/dev/null; then
                        brew install netcat || true
                    fi
                fi
                ;;
            "linux")
                case "$PKG_MANAGER" in
                    "apt")
                        sudo apt install -y netcat-openbsd || sudo apt install -y netcat || true
                        ;;
                    "yum")
                        sudo yum install -y nc || sudo yum install -y nmap-ncat || true
                        ;;
                    "pacman")
                        sudo pacman -S --noconfirm openbsd-netcat || true
                        ;;
                esac
                ;;
        esac
    fi
    
    case "$OS" in
        "macos")
            # Check for Xcode command line tools
            if ! xcode-select -p &>/dev/null; then
                log_step "Installing Xcode command line tools..."
                xcode-select --install
                log_warning "Please complete the Xcode installation and re-run this script"
                read -p "Press Enter after Xcode tools are installed..."
            fi
            ;;
        "linux")
            case "$PKG_MANAGER" in
                "apt")
                    log_step "Updating package lists..."
                    retry_command "sudo apt update" "Package list update"
                    retry_command "sudo apt install -y curl wget build-essential software-properties-common" "Basic build tools"
                    ;;
                "yum")
                    retry_command "sudo yum groupinstall -y 'Development Tools'" "Development tools"
                    retry_command "sudo yum install -y curl wget" "Basic utilities"
                    ;;
                "pacman")
                    retry_command "sudo pacman -Sy --noconfirm base-devel curl wget" "Basic build tools"
                    ;;
            esac
            ;;
    esac
}

# ── Install Python ─────────────────────────────────────────────────────────
install_python() {
    log_step "Setting up Python..."
    
    # Try to find existing Python installation
    for cmd in python3 python python3.12 python3.11 python3.10 python3.9; do
        if check_python_version "$cmd"; then
            return 0
        fi
    done
    
    # Install Python based on OS
    case "$OS" in
        "linux")
            case "$PKG_MANAGER" in
                "apt")
                    retry_command "sudo apt install -y python3 python3-pip python3-venv python3-dev" "Python installation"
                    ;;
                "yum")
                    retry_command "sudo yum install -y python3 python3-pip python3-venv python3-devel" "Python installation"
                    ;;
                "pacman")
                    retry_command "sudo pacman -S --noconfirm python python-pip" "Python installation"
                    ;;
            esac
            ;;
        "macos")
            if ! command -v brew &>/dev/null; then
                log_step "Installing Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
                # Add Homebrew to PATH for Apple Silicon
                if [[ -f "/opt/homebrew/bin/brew" ]]; then
                    eval "$(/opt/homebrew/bin/brew shellenv)"
                    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
                elif [[ -f "/usr/local/bin/brew" ]]; then
                    eval "$(/usr/local/bin/brew shellenv)"
                fi
            fi
            retry_command "brew install python@3.12" "Python installation"
            ;;
    esac
    
    # Verify installation
    for cmd in python3 python python3.12 python3.11 python3.10 python3.9; do
        if check_python_version "$cmd"; then
            return 0
        fi
    done
    
    error_exit "Python installation failed or version is incompatible"
}

# ── Install uv ─────────────────────────────────────────────────────────────
install_uv() {
    if command -v uv &>/dev/null; then
        log_success "uv is already installed"
        return 0
    fi
    
    log_step "Installing uv (fast Python package manager)..."
    retry_command "curl -LsSf https://astral.sh/uv/install.sh | sh" "uv installation"
    
    # Add uv to PATH
    export PATH="$HOME/.cargo/bin:$PATH"
    
    # Also add to shell profiles for future sessions
    for profile in ~/.bashrc ~/.zshrc ~/.profile; do
        if [[ -f "$profile" ]]; then
            if ! grep -q "/.cargo/bin" "$profile"; then
                echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> "$profile"
            fi
        fi
    done
    
    # Verify installation
    if ! command -v uv &>/dev/null; then
        error_exit "uv installation failed"
    fi
    
    log_success "uv installed successfully"
}

# ── Install FFmpeg ─────────────────────────────────────────────────────────
install_ffmpeg() {
    if command -v ffmpeg &>/dev/null; then
        log_success "FFmpeg is already installed"
        return 0
    fi
    
    log_step "Installing FFmpeg..."
    
    case "$OS" in
        "linux")
            case "$PKG_MANAGER" in
                "apt")
                    retry_command "sudo apt install -y ffmpeg" "FFmpeg installation"
                    ;;
                "yum")
                    # Enable EPEL for CentOS/RHEL
                    sudo yum install -y epel-release || true
                    retry_command "sudo yum install -y ffmpeg" "FFmpeg installation"
                    ;;
                "pacman")
                    retry_command "sudo pacman -S --noconfirm ffmpeg" "FFmpeg installation"
                    ;;
            esac
            ;;
        "macos")
            if command -v brew &>/dev/null; then
                retry_command "brew install ffmpeg" "FFmpeg installation"
            else
                log_warning "Homebrew not available, skipping FFmpeg installation"
            fi
            ;;
    esac
    
    # Verify installation
    if ! command -v ffmpeg &>/dev/null; then
        error_exit "FFmpeg installation failed"
    fi
    
    log_success "FFmpeg installed successfully"
}

# ── Install Node.js via nvm ────────────────────────────────────────────────
install_nodejs() {
    log_step "Setting up Node.js..."
    
    # Setup NVM environment
    export NVM_DIR="$HOME/.nvm"
    
    # Install nvm if not present
    if [ ! -d "$NVM_DIR" ]; then
        log_step "Installing nvm (Node Version Manager)..."
        retry_command "curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash" "nvm installation"
    fi
    
    # Source nvm
    if [ -s "$NVM_DIR/nvm.sh" ]; then
        # shellcheck disable=SC1090
        source "$NVM_DIR/nvm.sh"
    else
        error_exit "nvm installation failed - nvm.sh not found"
    fi
    
    # Install Node.js LTS
    if ! command -v node &>/dev/null; then
        log_step "Installing Node.js LTS..."
        retry_command "nvm install --lts" "Node.js LTS installation"
        retry_command "nvm use --lts" "Node.js LTS activation"
        # Set as default
        nvm alias default lts/*
    fi
    
    # Verify Node.js version
    local node_version
    node_version=$(node --version 2>/dev/null | sed 's/v//' || echo "0")
    if [ "$(printf '%s\n' "$NODE_MIN_VERSION" "$node_version" | sort -V | head -n1)" != "$NODE_MIN_VERSION" ]; then
        log_warning "Node.js version $node_version is below recommended $NODE_MIN_VERSION"
    fi
    
    log_success "Node.js $(node --version) installed successfully"
}

# ── Fix npm permissions ────────────────────────────────────────────────────
fix_npm_permissions() {
    log_step "Fixing npm permissions..."
    
    # Create npm global directory
    mkdir -p ~/.npm-global
    
    # Configure npm to use the new directory
    npm config set prefix '~/.npm-global'
    
    # Add to PATH for current session
    export PATH=~/.npm-global/bin:$PATH
    
    # Add to shell profiles for future sessions
    for profile in ~/.bashrc ~/.zshrc ~/.profile; do
        if [[ -f "$profile" ]]; then
            if ! grep -q "npm-global" "$profile"; then
                echo 'export PATH=~/.npm-global/bin:$PATH' >> "$profile"
            fi
        fi
    done
    
    log_success "npm permissions fixed"
}

# ── Install localtunnel ────────────────────────────────────────────────────
install_localtunnel() {
    if command -v lt &>/dev/null; then
        log_success "localtunnel is already installed"
        return 0
    fi
    
    # Fix npm permissions first
    fix_npm_permissions
    
    log_step "Installing localtunnel..."
    
    # Use retry mechanism but with better error handling
    local attempt=1
    while [ $attempt -le $RETRY_ATTEMPTS ]; do
        log_info "Attempting localtunnel installation (attempt $attempt/$RETRY_ATTEMPTS)"
        
        # Try installing with npm
        if npm install -g localtunnel; then
            log_success "localtunnel installed successfully"
            break
        fi
        
        log_warning "localtunnel installation failed on attempt $attempt"
        
        # If we're on the last attempt, try alternative methods
        if [ $attempt -eq $RETRY_ATTEMPTS ]; then
            log_info "Trying alternative installation methods..."
            
            # Try installing in local node_modules as last resort
            if npm install localtunnel; then
                log_success "localtunnel installed locally"
                # Create a symlink or alias
                mkdir -p ~/.local/bin
                echo '#!/bin/bash' > ~/.local/bin/lt
                echo "$(pwd)/node_modules/.bin/lt \$@" >> ~/.local/bin/lt
                chmod +x ~/.local/bin/lt
                export PATH="$HOME/.local/bin:$PATH"
                
                # Add to shell profiles
                for profile in ~/.bashrc ~/.zshrc ~/.profile; do
                    if [[ -f "$profile" ]]; then
                        if ! grep -q "/.local/bin" "$profile"; then
                            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$profile"
                        fi
                    fi
                done
                break
            fi
            
            error_exit "localtunnel installation failed after trying all methods"
        fi
        
        ((attempt++))
        sleep 2
    done
    
    # Verify installation
    if ! command -v lt &>/dev/null; then
        error_exit "localtunnel installation verification failed"
    fi
    
    log_success "localtunnel is ready to use"
}

# ── Setup Python virtual environment ──────────────────────────────────────
setup_python_env() {
    log_step "Setting up Python virtual environment..."
    
    # Create virtual environment
    if [ ! -d ".venv" ]; then
        retry_command "uv venv" "Python virtual environment creation"
    fi
    
    # Activate virtual environment
    if [ -f ".venv/bin/activate" ]; then
        # shellcheck disable=SC1091
        source .venv/bin/activate
        log_success "Virtual environment activated"
    else
        error_exit "Virtual environment activation failed"
    fi
    
    # Install dependencies
    if [ -f "pyproject.toml" ]; then
        log_step "Installing Python dependencies from pyproject.toml..."
        retry_command "uv pip install -e ." "Python dependencies installation"
    elif [ -f "requirements.txt" ]; then
        log_step "Installing Python dependencies from requirements.txt..."
        retry_command "uv pip install -r requirements.txt" "Python dependencies installation"
    else
        log_warning "No pyproject.toml or requirements.txt found - installing basic Streamlit"
        retry_command "uv pip install streamlit" "Streamlit installation"
    fi
    
    log_success "Python environment setup completed"
}

# ── Find free port ─────────────────────────────────────────────────────────
find_free_port() {
    local port=$1
    while lsof -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; do
        port=$((port + 1))
    done
    echo "$port"
}

# ── Wait for service to be ready ───────────────────────────────────────────
wait_for_service() {
    local port=$1
    local timeout=${2:-$TIMEOUT_SECONDS}
    local elapsed=0
    
    log_info "Waiting for service on port $port (timeout: ${timeout}s)..."
    
    while [ $elapsed -lt $timeout ]; do
        # Try multiple methods to check if port is open
        if nc -z 127.0.0.1 "$port" 2>/dev/null; then
            return 0
        elif command -v telnet &>/dev/null; then
            if echo "quit" | telnet 127.0.0.1 "$port" 2>/dev/null | grep -q "Connected"; then
                return 0
            fi
        elif command -v python3 &>/dev/null; then
            if python3 -c "import socket; sock = socket.socket(); sock.settimeout(1); result = sock.connect_ex(('127.0.0.1', $port)); sock.close(); exit(result)" 2>/dev/null; then
                return 0
            fi
        fi
        sleep 1
        elapsed=$((elapsed + 1))
    done
    
    error_exit "Service on port $port failed to start within ${timeout}s"
}

# ── Cleanup function ───────────────────────────────────────────────────────
cleanup() {
    # Stop sudo keep-alive
    stop_sudo_keepalive
    
    if [ ${#PIDS[@]} -gt 0 ] 2>/dev/null; then
        log_info "Shutting down services..."
        
        # Kill background processes
        for pid in "${PIDS[@]}"; do
            if kill -0 "$pid" 2>/dev/null; then
                log_info "Stopping process $pid..."
                kill "$pid" 2>/dev/null || true
            fi
        done
        
        # Wait for processes to terminate
        for pid in "${PIDS[@]}"; do
            wait "$pid" 2>/dev/null || true
        done
        
        log_success "All services stopped"
    fi
}

# ── Main execution ─────────────────────────────────────────────────────────
main() {
    # Change to script directory
    local script_dir
    script_dir="$(cd "$(dirname "$0")" && pwd)"
    cd "$script_dir" || error_exit "Failed to change to script directory"
    
    # Array to track background process PIDs
    PIDS=()
    
    # Setup signal handlers
    trap cleanup INT TERM EXIT
    
    # Show welcome message
    show_welcome
    
    # Request sudo permissions upfront
    request_sudo_upfront
    
    # System detection
    detect_system
    
    # Install all dependencies
    install_system_deps
    install_python
    install_uv
    install_ffmpeg
    install_nodejs
    install_localtunnel
    
    # Setup Python environment
    setup_python_env
    
    # Check if app file exists
    if [ ! -f "$APP_FILE" ]; then
        error_exit "Application file $APP_FILE not found in $(pwd)"
    fi
    
    # Find free ports
    STREAMLIT_PORT=$(find_free_port $BASE_PORT)
    DASHBOARD_PORT=$(find_free_port $UI_PORT)
    
    log_info "Using ports: Streamlit=$STREAMLIT_PORT, Dashboard=$DASHBOARD_PORT"
    
    # Start Streamlit
    log_step "Starting Streamlit application..."
    uv run streamlit run "$APP_FILE" --server.port "$STREAMLIT_PORT" --server.headless true &
    STREAMLIT_PID=$!
    PIDS[${#PIDS[@]}]="$STREAMLIT_PID"
    
    # Wait for Streamlit to be ready
    wait_for_service "$STREAMLIT_PORT"
    log_success "Streamlit is running at http://localhost:$STREAMLIT_PORT"
    
    # Start LocalTunnel
    log_step "Starting LocalTunnel..."
    lt --port "$STREAMLIT_PORT" --subdomain "$SUBDOMAIN" --host "$HOST" &
    LT_PID=$!
    PIDS[${#PIDS[@]}]="$LT_PID"
    
    # Wait a bit for tunnel to establish
    sleep 5
    
    # Get tunnel password
    local lt_password
    lt_password=$(curl -s --max-time 10 https://loca.lt/mytunnelpassword || echo "unavailable")
    log_success "LocalTunnel running at https://$SUBDOMAIN.loca.lt"
    log_info "Tunnel password: $lt_password"
    
    # Start dashboard if serve_ui.py exists
    if [ -f "serve_ui.py" ]; then
        log_step "Starting dashboard..."
        export APP_PORT="$STREAMLIT_PORT" SUBDOMAIN="$SUBDOMAIN" LT_PASSWORD="$lt_password"
        "$PYTHON_CMD" serve_ui.py --port "$DASHBOARD_PORT" &
        DASHBOARD_PID=$!
        PIDS[${#PIDS[@]}]="$DASHBOARD_PID"
        
        wait_for_service "$DASHBOARD_PORT"
        log_success "Dashboard running at http://localhost:$DASHBOARD_PORT"
        
        # Open browser
        if command -v open &>/dev/null; then
            open "http://localhost:$DASHBOARD_PORT" 2>/dev/null || true
        elif command -v xdg-open &>/dev/null; then
            xdg-open "http://localhost:$DASHBOARD_PORT" 2>/dev/null || true
        fi
    else
        # Open Streamlit directly if no dashboard
        if command -v open &>/dev/null; then
            open "http://localhost:$STREAMLIT_PORT" 2>/dev/null || true
        elif command -v xdg-open &>/dev/null; then
            xdg-open "http://localhost:$STREAMLIT_PORT" 2>/dev/null || true
        fi
    fi
    
    # Display summary
    echo
    echo -e "${GREEN}🎉 Setup completed successfully!${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}📊 Local Streamlit: http://localhost:$STREAMLIT_PORT${NC}"
    echo -e "${CYAN}🌐 Public URL: https://$SUBDOMAIN.loca.lt${NC}"
    echo -e "${CYAN}🔑 Tunnel Password: $lt_password${NC}"
    if [ -f "serve_ui.py" ]; then
        echo -e "${CYAN}📋 Dashboard: http://localhost:$DASHBOARD_PORT${NC}"
    fi
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo
    
    echo -e "${YELLOW}The application is now running. Press Ctrl+C to stop all services.${NC}"
    echo -e "${YELLOW}You can close this terminal window and the services will continue running.${NC}"
    echo
    
    # Stop sudo keep-alive since we don't need it anymore
    stop_sudo_keepalive
    
    # Wait for main process
    wait "$STREAMLIT_PID"
}

# ── Script entry point ─────────────────────────────────────────────────────
# Ensure the script runs from the correct directory
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi