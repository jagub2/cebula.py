FROM python:3.9-alpine

COPY requirements.txt ./
RUN apk add --no-cache --virtual .build-deps gcc musl-dev libc-dev libxslt-dev libressl-dev libffi-dev && \
    apk add --no-cache libxslt ca-certificates && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del .build-deps && \
    addgroup -S cebula && \
    adduser -S cebula -G cebula

USER cebula

COPY . /app
WORKDIR /app

ENTRYPOINT ["python", "-u", "/app/cebula.py"]

