#!/bin/bash
# start.sh - Auto fix and start application

echo "🔧 Running auto error fixer..."
python auto_error_fixer.py

echo "🚀 Starting application..."
uvicorn kinva_master:app --host 0.0.0.0 --port $PORT
