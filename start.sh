#!/bin/bash

echo "Starting Multi-Site Inventory Analysis Dashboard..."
echo "=================================================="
echo ""
echo "Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "Starting Flask server..."
echo "Dashboard will be available at: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 app.py


