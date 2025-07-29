#!/bin/bash
# setup.sh - Xinch Project Setup Script

set -e  # Exit on any error

echo "🚀 Xinch Setup Script"
echo "====================="
echo "Setting up cross-chain USDC swap environment..."
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m' 
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if Python 3.8+ is installed
echo "🔍 Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [[ $PYTHON_MAJOR -ge 3 && $PYTHON_MINOR -ge 8 ]]; then
        print_status "Python $PYTHON_VERSION found"
    else
        print_error "Python 3.8+ required, found $PYTHON_VERSION"
        exit 1
    fi
else
    print_error "Python 3 not found. Please install Python 3.8+"
    exit 1
fi

# Check if pip is installed
echo "🔍 Checking pip..."
if command -v pip3 &> /dev/null; then
    print_status "pip3 found"
    PIP_CMD="pip3"
elif command -v pip &> /dev/null; then
    print_status "pip found"
    PIP_CMD="pip"
else
    print_error "pip not found. Please install pip"
    exit 1
fi

# Check if Foundry is installed
echo "🔍 Checking Foundry installation..."
if command -v forge &> /dev/null; then
    FORGE_VERSION=$(forge --version | head -n1)
    print_status "Foundry found: $FORGE_VERSION"
else
    print_warning "Foundry not found. Installing Foundry..."
    
    # Install Foundry
    curl -L https://foundry.paradigm.xyz | bash
    source ~/.bashrc 2>/dev/null || source ~/.bash_profile 2>/dev/null || true
    foundryup
    
    if command -v forge &> /dev/null; then
        print_status "Foundry installed successfully"
    else
        print_error "Foundry installation failed. Please install manually from https://book.getfoundry.sh/"
        print_info "After installation, run: source ~/.bashrc && foundryup"
        exit 1
    fi
fi

# Setup Python virtual environment
echo "🐍 Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    print_info "Creating virtual environment 'venv'..."
    python3 -m venv venv
    print_status "Virtual environment created."
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate
print_status "Virtual environment activated."

# Upgrade pip within the venv
pip install --upgrade pip > /dev/null

# Install Python dependencies
echo "📦 Installing Python dependencies into venv..."
if [[ -f "requirements.txt" ]]; then
    pip install -r requirements.txt
    print_status "Python dependencies installed"
else
    print_error "requirements.txt not found"
    exit 1
fi

# Install OpenZeppelin contracts
echo "📦 Installing OpenZeppelin contracts..."
if [[ ! -d ".git" ]]; then
    print_warning "Not a git repository. Initializing one now..."
    git init > /dev/null
    print_status "Git repository initialized."
fi

print_info "Installing/updating OpenZeppelin contracts..."
if forge install OpenZeppelin/openzeppelin-contracts; then
    print_status "OpenZeppelin contracts installed."
else
    print_error "Failed to install OpenZeppelin contracts with forge."
    exit 1
fi

# Verify a key file exists to ensure installation was correct
OZ_GUARD_PATH="lib/openzeppelin-contracts/contracts/utils/ReentrancyGuard.sol"
print_info "Verifying that OpenZeppelin files exist..."
if [ ! -f "$OZ_GUARD_PATH" ]; then
    print_error "Installation check failed: ReentrancyGuard.sol not found."
    print_info "Expected path: $OZ_GUARD_PATH"
    print_info "This can happen if the library version has a different folder structure."
    print_info "Listing contents of lib/ for debugging:"
    ls -R lib/
    exit 1
fi
print_status "OpenZeppelin installation verified."

# Compile smart contracts
echo "🔨 Compiling smart contracts..."
if forge build; then
    print_status "Smart contracts compiled successfully"
else
    print_error "Smart contract compilation failed"
    print_info "Make sure OpenZeppelin contracts are installed"
    exit 1
fi

# Check if .env exists, if not create from example
echo "⚙️  Setting up environment configuration..."
if [[ ! -f ".env" ]]; then
    if [[ -f ".env.example" ]]; then
        cp .env.example .env
        print_status "Created .env from .env.example"
        print_warning "Please edit .env file with your actual configuration"
    else
        # Create a basic .env file
        cat > .env << 'EOF'
# Xinch Configuration
# Edit these values with your actual credentials

# Ethereum Configuration (Sepolia testnet)
ETH_RPC_URL=https://sepolia.infura.io/v3/YOUR_INFURA_PROJECT_ID
ETH_PRIVATE_KEY=0xYOUR_ETHEREUM_PRIVATE_KEY_HERE
ESCROW_CONTRACT_ADDRESS=

# XRPL Configuration (Testnet)
XRPL_RPC_URL=wss://s.altnet.rippletest.net:51233
XRPL_WALLET_SEED=sYOUR_XRPL_WALLET_SEED_HERE

# Token Testnet Addresses
ETH_USDC_ADDRESS=0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238
XRPL_USDC_ISSUER=rHuGNhqTG32mfmAvWA8hUyWRLV3tCSwKQt
EOF
        print_status "Created basic .env file"
        print_warning "Please edit .env file with your actual configuration"
    fi
else
    print_status ".env file already exists"
fi

# Run tests to verify setup
echo "🧪 Running tests to verify setup..."
if python3 -m pytest tests/ -v --tb=short; then
    print_status "All tests passed! Setup verification successful"
else
    print_warning "Some tests failed. This might be due to missing configuration."
    print_info "Please configure your .env file and try running tests again"
fi

# Final instructions
echo
echo "🎉 Setup Complete!"
echo "=================="
echo
echo "Next steps:"
echo "1. 📝 Edit .env file with your credentials:"
echo "   - Get Ethereum RPC URL from Infura/Alchemy"
echo "   - Add your Ethereum private key (testnet only!)"
echo "   - Add your XRPL wallet seed"
echo
echo "2. 🚀 Deploy smart contracts:"
echo "   python scripts/deploy.py"
echo
echo "3. 🧪 Run tests:"
echo "   python -m pytest tests/ -v"
echo
echo "4. 💱 Execute swaps:"
echo "   python src/main.py"
echo
echo "5. 📖 Read the documentation:"
echo "   cat README.md"
echo

# Check for common issues
echo "🔍 System Check:"
echo "==============="

# Check git
if command -v git &> /dev/null; then
    print_status "Git is available"
else
    print_warning "Git not found - needed for dependency management"
fi

# Check node (optional for XRPL)
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    print_status "Node.js found: $NODE_VERSION"
else
    print_info "Node.js not found (optional for XRPL development)"
fi

# Check available disk space
AVAILABLE_SPACE=$(df -h . | awk 'NR==2 {print $4}')
print_info "Available disk space: $AVAILABLE_SPACE"

echo
print_status "Setup script completed successfully!"
print_info "If you encounter any issues, check the README.md for troubleshooting" 