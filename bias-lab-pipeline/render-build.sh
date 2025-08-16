#!/usr/bin/env bash
set -e

echo "🔧 Starting Render build for Bias Lab Pipeline..."

# Update system packages
echo "📦 Installing system dependencies..."
apt-get update -qq
apt-get install -y build-essential python3-dev libffi-dev libssl-dev

# Install Python dependencies with timeout and retries
echo "🐍 Installing Python packages..."
pip install --upgrade pip setuptools wheel

# Install spaCy first with specific timeout
echo "🧠 Installing spaCy..."
pip install --timeout=600 spacy>=3.7.0,<3.8.0

# Download spaCy model directly
echo "📚 Downloading spaCy English model..."
python -m spacy download en_core_web_sm --timeout=600

# Install remaining requirements
echo "📋 Installing remaining requirements..."
pip install --timeout=600 -r requirements.txt

echo "✅ Build completed successfully!"
