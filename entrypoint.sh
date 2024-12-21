#!/bin/sh

if [ -z "$PUID" ] || [ -z "$PGID" ]; then
  exec uvicorn ubiblio.main:app --host 0.0.0.0 --port 8000 --forwarded-allow-ips '*' --proxy-headers
else
  adduser -u $PUID -D abc
  groupmod -g $PGID abc

  chown abc:abc -R /app

  exec su-exec abc uvicorn ubiblio.main:app --host 0.0.0.0 --port 8000 --forwarded-allow-ips '*' --proxy-headers
fi
