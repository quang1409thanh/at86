#!/bin/bash
trap "kill 0" EXIT

echo "Starting TOEIC Platform..."

# Start Backend
cd backend
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Virtual environment not found, creating..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
echo "Backend started on port 8000 (PID: $BACKEND_PID)"

# Start Frontend
cd ../frontend
if [ ! -d "node_modules" ]; then
    echo "Node modules not found, installing..."
    npm install
fi

npm run dev -- --host &
FRONTEND_PID=$!
echo "Frontend started on port 5173 (PID: $FRONTEND_PID)"

wait
