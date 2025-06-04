#!/bin/bash

echo "🐅 TigerGraph Social Network Chatbot Setup"
echo "=========================================="

# Check if Python 3.8+ is installed
python_version=$(python3 --version 2>&1 | grep -Po '(?<=Python )(.+)')
if [[ -z "$python_version" ]]; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or later."
    exit 1
fi

echo "✅ Python $python_version found"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install requirements
echo "📥 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating project structure..."
mkdir -p templates
mkdir -p static
mkdir -p logs

# Copy environment template
if [ ! -f .env ]; then
    cp .env.template .env
    echo "📋 Created .env file from template. Please edit it with your credentials."
else
    echo "⚠️  .env file already exists. Please verify your configuration."
fi

echo ""
echo "🎉 Setup complete! Next steps:"
echo ""
echo "1. 🔧 Configure TigerGraph:"
echo "   - Make sure TigerGraph is running"
echo "   - Run the GSQL script: setup_tigergraph.gsql"
echo "   - Update .env with your TigerGraph connection details"
echo ""
echo "2. ☁️  Configure Azure OpenAI:"
echo "   - Create an Azure OpenAI resource"
echo "   - Deploy GPT-4 and text-embedding-ada-002 models"
echo "   - Update .env with your Azure OpenAI credentials"
echo ""
echo "3. 🚀 Run the application:"
echo "   source venv/bin/activate"
echo "   python app.py"
echo ""
echo "4. 🌐 Open your browser to: http://localhost:5000"
echo ""