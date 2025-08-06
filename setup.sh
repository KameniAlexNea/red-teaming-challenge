#!/bin/bash

# Setup script for the red-teaming agent

set -e

echo "🚀 Setting up Red-Teaming Agent for GPT-OSS-20B"
echo "================================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
required_version="3.8"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "❌ Python 3.8+ is required, but found Python $python_version"
    exit 1
fi

echo "✅ Python $python_version found"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📥 Installing Python dependencies..."
pip install -r requirements.txt

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "⚠️  Ollama is not installed. Please install it from https://ollama.ai"
    echo "   Run: curl -fsSL https://ollama.ai/install.sh | sh"
    echo ""
    echo "   After installation, start Ollama with: ollama serve"
    echo "   Then pull required models:"
    echo "   - ollama pull llama3.1:latest"
    echo "   - ollama pull gpt-oss-20b  # When available"
else
    echo "✅ Ollama found"
    
    # Check if Ollama is running
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama is running"
        
        # Check for required models
        echo "🔍 Checking for required models..."
        
        if ollama list | grep -q "llama3.1:latest"; then
            echo "✅ llama3.1:latest model found"
        else
            echo "📥 Pulling llama3.1:latest model..."
            ollama pull llama3.1:latest
        fi
        
        if ollama list | grep -q "gpt-oss-20b"; then
            echo "✅ gpt-oss-20b model found"
        else
            echo "⚠️  gpt-oss-20b model not found"
            echo "   This model may not be available yet. You can:"
            echo "   1. Wait for the model to be released"
            echo "   2. Use a substitute model for testing"
            echo "   3. Pull it manually when available: ollama pull gpt-oss-20b"
        fi
        
    else
        echo "⚠️  Ollama is not running. Start it with: ollama serve"
    fi
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📄 Creating .env file from template..."
    cp .env.example .env
    echo "✅ Created .env file. Please review and modify if needed."
fi

# Create output directory
echo "📁 Creating output directory..."
mkdir -p red_teaming_results

# Run validation
echo "🔧 Validating setup..."
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from alex_red_teaming.config import Config
    config = Config.from_env()
    print('✅ Configuration loaded successfully')
except Exception as e:
    print(f'⚠️  Configuration warning: {e}')
"

echo ""
echo "🎉 Setup completed!"
echo ""
echo "Next steps:"
echo "1. Ensure Ollama is running: ollama serve"
echo "2. Pull required models (if not already done):"
echo "   - ollama pull llama3.1:latest"
echo "   - ollama pull gpt-oss-20b  # When available"
echo "3. Review the .env file for configuration"
echo "4. Run the agent: python main.py"
echo ""
echo "For more options, see: python -m alex_red_teaming.cli --help"
