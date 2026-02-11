#!/bin/bash
# Build script for Railpack

set -e

echo "🏗️ Building Crypto Signal Scanner..."

# Install Python dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Build complete!"
