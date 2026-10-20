FROM ghcr.io/astral-sh/uv:0.12.4 AS uv
FROM python:3.14-slim

COPY --from=uv /uv /bin/uv
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY . .
RUN uv sync --locked --no-dev --no-editable

ENV PATH="/app/.venv/bin:$PATH"
ENTRYPOINT ["python"]
CMD ["examples/example_easy.py"]
