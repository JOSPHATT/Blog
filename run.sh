#!/bin/bash

echo "🏆 Starting Team Analysis Blog Flask Application..."
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python3 first."
    exit 1
fi

# Check if Flask is installed
if ! python3 -c "import flask" &> /dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt --break-system-packages
    echo ""
fi

echo "🚀 Starting Flask application on http://localhost:5000"
echo ""
echo "Available endpoints:"
echo "  • Homepage: http://localhost:5000/"
echo "  • Teams:    http://localhost:5000/teams"
echo "  • Search:   http://localhost:5000/search"
echo "  • API:      http://localhost:5000/api/posts"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the Flask application
python3 app.py