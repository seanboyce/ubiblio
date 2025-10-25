#!/bin/sh

# Development mode: if DEV=true, run uvicorn with reload and do not change ownership
if [ "$DEV" = "true" ] || [ "$DEV" = "1" ]; then
  exec uvicorn ubiblio.main:app --host 0.0.0.0 --port 8000 --reload --forwarded-allow-ips '*' --proxy-headers
fi

# Production/default behaviour: create user if PUID/PGID are provided and run as that user
if [ -z "$PUID" ] || [ -z "$PGID" ]; then
  exec uvicorn ubiblio.main:app --host 0.0.0.0 --port 8000 --forwarded-allow-ips '*' --proxy-headers
else
  adduser -u $PUID -D abc
  groupmod -g $PGID abc

  chown abc:abc -R /app

  exec su-exec abc uvicorn ubiblio.main:app --host 0.0.0.0 --port 8000 --forwarded-allow-ips '*' --proxy-headers
fi
