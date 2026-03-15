#!/bin/bash
echo "=== Seeding Qdrant ==="
python seed_qdrant.py
echo "=== Starting THEMIS ==="
uvicorn api.main:app --host 0.0.0.0 --port 7860