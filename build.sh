#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Create uploads directory
mkdir -p uploads

# Initialize database
python -c "from app import db; db.create_all()"
