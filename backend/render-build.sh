#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt

# Any extra build steps (e.g. collecting static files if needed)
# For this project, we just need to ensure the uploads and ml_models directories exist
mkdir -p backend/uploads
mkdir -p backend/ml_models

echo "Build complete!"
