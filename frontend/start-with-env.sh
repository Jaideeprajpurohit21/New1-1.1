#!/bin/bash
# Frontend startup script with guaranteed environment variables

export REACT_APP_BACKEND_URL="https://bill-tracker-102.preview.emergentagent.com"
export HOST="0.0.0.0"
export PORT="3000"
export BROWSER="none"

echo "🔧 Starting frontend with environment:"
echo "  REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL"
echo "  HOST=$HOST"  
echo "  PORT=$PORT"

cd /app/frontend
exec yarn start