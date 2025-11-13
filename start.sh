#!/bin/bash
# Start script for Second Brain PoC

cd "$(dirname "$0")"

echo "🧠 Starting Second Brain PoC..."
echo ""

# Check if Ollama is running
if ! pgrep -x "ollama" > /dev/null; then
    echo "⚠️  Ollama is not running. Starting it..."
    brew services start ollama
    sleep 3
fi

# Check if model is available
if ! ollama list | grep -q "qwen2.5:7b-instruct"; then
    echo "❌ Qwen model not found. Please run: ollama pull qwen2.5:7b-instruct"
    exit 1
fi

# Activate virtual environment
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Creating it..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Start the orchestrator
echo "✅ All checks passed. Starting orchestrator..."
echo ""
python3 orchestrator.py
