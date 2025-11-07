#!/usr/bin/env bash
set -euo pipefail

REDIS_PASSWORD=${REDIS_PASSWORD:-demo123}

# Start Redis in background and wait for readiness
redis-server --daemonize yes --appendonly yes --protected-mode yes \
  --bind 127.0.0.1 --requirepass "$REDIS_PASSWORD" --dir /data --pidfile /tmp/redis.pid

for i in {1..40}; do
  if redis-cli -a "$REDIS_PASSWORD" -h 127.0.0.1 -p 6379 ping >/dev/null 2>&1; then
    echo "Redis is up"
    break
  fi
  sleep 0.25
done

exec uvicorn app.main:app --host 0.0.0.0 --port 8080


