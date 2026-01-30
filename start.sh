#!/bin/bash

# Define colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to kill processes on ports
cleanup_ports() {
    echo -e "${YELLOW}[*] Checking ports 8000 and 5173...${NC}"
    for PORT in 8000 5173; do
        # Find PID using lsof or fuser
        PID=$(lsof -ti:$PORT 2>/dev/null)
        if [ -n "$PID" ]; then
            echo -e "${RED}[!] Port $PORT is in use by PID $PID. Killing...${NC}"
            kill -9 $PID 2>/dev/null
        fi
    done
}

# Function to handle script exit
cleanup() {
    echo -e "\n${RED}[!] Stopping services...${NC}"
    # Kill all child processes of this script
    kill $(jobs -p) 2>/dev/null
    exit
}

# Trap signals for cleanup
trap cleanup SIGINT SIGTERM EXIT

# Header
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Starting TOEIC Platform System       ${NC}"
echo -e "${GREEN}========================================${NC}"

# 1. Cleanup old processes to avoid conflicts
cleanup_ports

# 2. Start Backend
echo -e "\n${GREEN}[*] Setting up Backend...${NC}"
cd backend || { echo "Backend directory not found!"; exit 1; }

# Virtual Environment Check
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
fi

# Activate and Install Deps
source venv/bin/activate
echo "Installing/Updating Python dependencies (this may take a moment)..."
pip install -r requirements.txt > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install python dependencies.${NC}"
    exit 1
fi

# Start Uvicorn
echo "Starting FastAPI Server..."
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo -e "${GREEN}[+] Backend running on http://localhost:8000 (PID: $BACKEND_PID)${NC}"

# 3. Start Frontend
cd ../frontend || { echo "Frontend directory not found!"; exit 1; }
echo -e "\n${GREEN}[*] Setting up Frontend...${NC}"

# Node Modules Check
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Node modules not found. Installing...${NC}"
    npm install > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to install node modules.${NC}"
        exit 1
    fi
fi

# Start Vite
echo "Starting Vite Server..."
npm run dev -- --host &
FRONTEND_PID=$!
echo -e "${GREEN}[+] Frontend running on http://localhost:5173 (PID: $FRONTEND_PID)${NC}"

# 4. Final Status
echo -e "\n${GREEN}[SUCCESS] System is live!${NC}"
echo -e "Frontend: ${GREEN}http://localhost:5173${NC}"
echo -e "Backend:  ${GREEN}http://localhost:8000/docs${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop all services.${NC}"

# Wait for infinite blocking
wait
