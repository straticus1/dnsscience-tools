#!/usr/bin/env bash
#
# DNSScience Tools - Unified Installer
# Installs all tools from the dnsscience-tools suite
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

show_help() {
    cat << EOF
DNSScience Tools - Unified Installer

Usage: $0 [OPTIONS]

Options:
    --all           Install all tools (default)
    --venv          Use virtual environment (default)
    --system        Install system-wide (requires sudo)
    --user          Install to user directory
    --symlink       Create symlinks in /usr/local/bin
    --submodules    Initialize/update git submodules only
    --dnsscience    Install only dnsscience-util
    --dnsnet        Install only DNSNet
    --globaldetect  Install only GlobalDetect
    --rancid        Install only RANCID-NG
    --help          Show this help message

Examples:
    $0 --all --venv          # Install all tools in virtual environment
    $0 --all --symlink       # Install all and create symlinks
    $0 --submodules          # Just update submodules
    $0 --dnsnet --venv       # Install only DNSNet
EOF
}

init_submodules() {
    log_info "Initializing git submodules..."
    cd "$SCRIPT_DIR"
    git submodule update --init --recursive
    log_success "Submodules initialized"
}

create_venv() {
    if [[ ! -d "$VENV_DIR" ]]; then
        log_info "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
        log_success "Virtual environment created at $VENV_DIR"
    fi
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip wheel setuptools
}

install_dnsscience_util() {
    log_info "Installing dnsscience-util..."
    cd "$SCRIPT_DIR"
    if [[ -n "$USE_VENV" ]]; then
        pip install -r requirements.txt
    elif [[ -n "$SYSTEM_INSTALL" ]]; then
        sudo pip install -r requirements.txt
    else
        pip install --user -r requirements.txt
    fi
    log_success "dnsscience-util installed"
}

install_dnsnet() {
    log_info "Installing DNSNet..."
    cd "$SCRIPT_DIR/submodules/dnsnet"

    if [[ ! -d "src" ]]; then
        log_warn "DNSNet source not found. Skipping."
        return
    fi

    if [[ -n "$USE_VENV" ]]; then
        pip install -e .
    elif [[ -n "$SYSTEM_INSTALL" ]]; then
        sudo pip install .
    else
        pip install --user -e .
    fi
    log_success "DNSNet installed"
}

install_globaldetect() {
    log_info "Installing GlobalDetect..."
    cd "$SCRIPT_DIR/submodules/globaldetect"

    if [[ ! -f "globaldetect" ]]; then
        log_warn "GlobalDetect not found. Skipping."
        return
    fi

    if [[ -f "install.sh" ]]; then
        if [[ -n "$USE_VENV" ]]; then
            ./install.sh --venv
        elif [[ -n "$SYSTEM_INSTALL" ]]; then
            sudo ./install.sh --system
        else
            ./install.sh --user
        fi
    else
        pip install -e .
    fi
    log_success "GlobalDetect installed"
}

install_rancid() {
    log_info "Installing RANCID-NG..."
    cd "$SCRIPT_DIR/submodules/rancid-ng"

    if [[ ! -f "pyproject.toml" ]]; then
        log_warn "RANCID-NG pyproject.toml not found. Skipping."
        return
    fi

    if [[ -n "$USE_VENV" ]]; then
        pip install -e .
    elif [[ -n "$SYSTEM_INSTALL" ]]; then
        sudo pip install .
    else
        pip install --user -e .
    fi
    log_success "RANCID-NG installed"
}

create_symlinks() {
    log_info "Creating symlinks in /usr/local/bin..."

    local tools=(
        "dnsscience-util.py:dnsscience-util"
        "dns4.py:dns4"
        "dns_compare.py:dns-compare"
        "dns_cache_validator.py:dns-cache-validator"
        "visual_traceroute.py:visual-traceroute"
    )

    for tool_pair in "${tools[@]}"; do
        local src="${tool_pair%%:*}"
        local dst="${tool_pair##*:}"
        if [[ -f "$SCRIPT_DIR/$src" ]]; then
            sudo ln -sf "$SCRIPT_DIR/$src" "/usr/local/bin/$dst"
            log_success "Linked $dst"
        fi
    done

    # Submodule tools
    if [[ -f "$SCRIPT_DIR/submodules/dnsnet/dnsnet" ]]; then
        sudo ln -sf "$SCRIPT_DIR/submodules/dnsnet/dnsnet" /usr/local/bin/dnsnet
        log_success "Linked dnsnet"
    fi

    if [[ -f "$SCRIPT_DIR/submodules/globaldetect/globaldetect" ]]; then
        sudo ln -sf "$SCRIPT_DIR/submodules/globaldetect/globaldetect" /usr/local/bin/globaldetect
        sudo ln -sf "$SCRIPT_DIR/submodules/globaldetect/globaldetect" /usr/local/bin/globalconnect
        log_success "Linked globaldetect/globalconnect"
    fi

    if [[ -f "$SCRIPT_DIR/submodules/rancid-ng/bin/rancid-ng" ]]; then
        for cmd in rancid-ng rancid clogin jlogin hlogin flogin panlogin fnlogin noklogin mtlogin xilogin; do
            if [[ -f "$SCRIPT_DIR/submodules/rancid-ng/bin/$cmd" ]]; then
                sudo ln -sf "$SCRIPT_DIR/submodules/rancid-ng/bin/$cmd" "/usr/local/bin/$cmd"
            fi
        done
        log_success "Linked RANCID-NG tools"
    fi
}

print_summary() {
    echo ""
    echo "================================================================"
    echo "  DNSScience Tools Installation Complete"
    echo "================================================================"
    echo ""
    echo "Installed tools:"
    echo ""
    echo "  Core DNS Tools:"
    echo "    dnsscience-util  - Advanced DNS analysis & security tool"
    echo "    dns4             - Fast DNS lookups"
    echo "    dns-compare      - Compare DNS configurations"
    echo "    visual-traceroute - Visual network path tracing"
    echo ""
    echo "  DNSNet:"
    echo "    dnsnet           - Enterprise DNS/DHCP/IPAM management"
    echo ""
    echo "  GlobalDetect:"
    echo "    globaldetect     - ISP network engineering utilities"
    echo "    globalconnect    - (alias for globaldetect)"
    echo ""
    echo "  RANCID-NG:"
    echo "    rancid-ng        - Network config backup & diff"
    echo "    clogin           - Cisco interactive login"
    echo "    jlogin           - Juniper interactive login"
    echo "    (and more vendor-specific login scripts)"
    echo ""

    if [[ -n "$USE_VENV" ]]; then
        echo "Virtual environment: $VENV_DIR"
        echo "Activate with: source $VENV_DIR/bin/activate"
    fi
    echo ""
}

# Parse arguments
USE_VENV=1
SYSTEM_INSTALL=""
USER_INSTALL=""
CREATE_SYMLINKS=""
SUBMODULES_ONLY=""
INSTALL_ALL=1
INSTALL_DNSSCIENCE=""
INSTALL_DNSNET=""
INSTALL_GLOBALDETECT=""
INSTALL_RANCID=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h) show_help; exit 0 ;;
        --all) INSTALL_ALL=1 ;;
        --venv) USE_VENV=1; SYSTEM_INSTALL=""; USER_INSTALL="" ;;
        --system) SYSTEM_INSTALL=1; USE_VENV=""; USER_INSTALL="" ;;
        --user) USER_INSTALL=1; USE_VENV=""; SYSTEM_INSTALL="" ;;
        --symlink) CREATE_SYMLINKS=1 ;;
        --submodules) SUBMODULES_ONLY=1 ;;
        --dnsscience) INSTALL_DNSSCIENCE=1; INSTALL_ALL="" ;;
        --dnsnet) INSTALL_DNSNET=1; INSTALL_ALL="" ;;
        --globaldetect) INSTALL_GLOBALDETECT=1; INSTALL_ALL="" ;;
        --rancid) INSTALL_RANCID=1; INSTALL_ALL="" ;;
        *) log_error "Unknown option: $1"; show_help; exit 1 ;;
    esac
    shift
done

# Execute
init_submodules

if [[ -n "$SUBMODULES_ONLY" ]]; then
    log_success "Submodules updated. Done."
    exit 0
fi

if [[ -n "$USE_VENV" ]]; then
    create_venv
fi

if [[ -n "$INSTALL_ALL" ]]; then
    install_dnsscience_util
    install_dnsnet
    install_globaldetect
    install_rancid
else
    [[ -n "$INSTALL_DNSSCIENCE" ]] && install_dnsscience_util
    [[ -n "$INSTALL_DNSNET" ]] && install_dnsnet
    [[ -n "$INSTALL_GLOBALDETECT" ]] && install_globaldetect
    [[ -n "$INSTALL_RANCID" ]] && install_rancid
fi

if [[ -n "$CREATE_SYMLINKS" ]]; then
    create_symlinks
fi

print_summary
