#!/bin/bash
# CoTA one-shot setup — install deps, ingest syllabus, launch app
set -e

echo "🎓 CoTA Setup — DATA643 Time Series Analysis"
echo ""

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ ANTHROPIC_API_KEY is not set."
    echo "   Run: export ANTHROPIC_API_KEY=your_key_here"
    echo "   Then: ./run.sh"
    exit 1
fi

echo "📦 Installing dependencies (this may take a minute)..."
pip install -q -r requirements.txt

echo ""
echo "🔧 Ingesting syllabus into ChromaDB..."
python ingest.py

echo ""
echo "🚀 Launching CoTA..."
streamlit run app.py
