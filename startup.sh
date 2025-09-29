#!/bin/bash

# Azure App Service startup script for FastAPI
echo "Starting Intelligence Ingestor..."

# Set the port from Azure environment variable
export PORT=${PORT:-8000}

echo "Using port: $PORT"

# Start the FastAPI application with Gunicorn
python -m gunicorn main:app --bind 0.0.0.0:$PORT --worker-class uvicorn.workers.UvicornWorker --workers 1