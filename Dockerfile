# syntax=docker/dockerfile:1
# check=skip=SecretsUsedInArgOrEnv

FROM alpine:3.19.4

RUN apk add --update python3 python3-dev alpine-sdk py3-pip openssl su-exec shadow zlib-dev libjpeg-turbo-dev gcc

RUN rm -rf /var/cache/apk/*

RUN mkdir /app

WORKDIR /app

COPY . .

RUN \
  cd /app && \
  pip install -r requirements.txt --break-system-packages

RUN chmod +x entrypoint.sh

ENV SECRET_KEY_FILE="/app/config/secret_key.txt"
ENV DB_LOCATION="./config/sql_app.db"
ENV USE_REDIS="false"

ENTRYPOINT ["./entrypoint.sh"]
