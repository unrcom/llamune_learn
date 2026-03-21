#!/bin/bash
cd /Users/mini/dev/llamune_learn
source .venv/bin/activate
exec python -m uvicorn app.main:app \
  --host 0.0.0.0 \
  --port ${PORT:-8100} \
  --log-config /Users/mini/dev/llamune_learn/log_config.json
