#!/bin/bash
# bootstrap.sh — run from project root to set up everything
set -e

echo "=== Financial Report Analyst — Bootstrap ==="

echo ""
echo "[ 1/5 ] Setting up Python virtual environment..."
cd backend
python3 -m venv venv
source venv/bin/activate

echo "[ 2/5 ] Installing Python dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo "[ 3/5 ] Creating required directories..."
mkdir -p data/uploads logs

echo "[ 4/5 ] Setting up environment file..."
if [ ! -f .env ]; then
  cp .env.example .env
  echo "  Created backend/.env — add your LLM and Neo4j settings before running"
else
  echo "  backend/.env already exists"
fi

cd ..

echo ""
echo "[ 5/5 ] Installing Node dependencies..."
cd frontend
npm install --silent
if [ ! -f .env ]; then
  echo "REACT_APP_API_URL=http://localhost:8000" > .env
  echo "  Created frontend/.env"
fi
cd ..

echo ""
echo "=== Bootstrap complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit backend/.env — set your LLM keys and Neo4j settings"
echo "  2. Terminal 1: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "  3. Terminal 2: cd frontend && npm start"
echo "  4. Open http://localhost:3000"
