FROM python:3.12-slim-bookworm

WORKDIR /app
ENV PYTHONUNBUFFERED=1

ARG PIP_INDEX_URL
ARG PIP_TRUSTED_HOST

COPY requirements.txt .
RUN set -e; \
    if [ -n "$PIP_INDEX_URL" ]; then \
      if [ -n "$PIP_TRUSTED_HOST" ]; then \
        pip install --no-cache-dir --no-compile -i "$PIP_INDEX_URL" --trusted-host "$PIP_TRUSTED_HOST" -r requirements.txt; \
      else \
        pip install --no-cache-dir --no-compile -i "$PIP_INDEX_URL" -r requirements.txt; \
      fi; \
    else \
      pip install --no-cache-dir --no-compile -r requirements.txt; \
    fi

COPY app ./app

EXPOSE 8008

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8008"]
