#!/bin/bash
cd /Users/mini/dev/llamune_learn
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8100
