#!/bin/bash

echo "🚀 Starting OLA AI Concierge..."

# Check if model exists
if [ ! -f "model/mistral-7b-instruct-v0.2.Q4_K_M.gguf" ]; then
    echo "❌ Model file not found!"
    echo "📥 Please download the model and place it in the 'model' folder"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
cd backend
pip install -r requirements.txt

# Start server
echo "✅ Starting server..."
python app.py