# ── Stage 1: Python 3.13 + task-runner-python setup ──────────────────────────
FROM python:3.13-alpine AS python-builder

RUN apk add --no-cache git

# Sparse-clone only the task-runner-python package at the exact n8n version
RUN git clone --filter=blob:none --sparse --depth=1 \
      --branch "n8n@2.15.0" \
      https://github.com/n8n-io/n8n.git /n8n-src && \
    cd /n8n-src && \
    git sparse-checkout set "packages/@n8n/task-runner-python"

# Create venv and install the task-runner-python package with its dependencies
WORKDIR /n8n-src/packages/@n8n/task-runner-python
RUN python3 -m venv .venv && \
    .venv/bin/pip install --no-cache-dir .

# ── Stage 2: Final n8n image ──────────────────────────────────────────────────
FROM n8nio/n8n:latest
USER root

# Copy Python 3.13 binaries
COPY --from=python-builder /usr/local/bin/python3.13 /usr/local/bin/python3.13
COPY --from=python-builder /usr/local/bin/python3    /usr/local/bin/python3
COPY --from=python-builder /usr/local/bin/python     /usr/local/bin/python

# Copy Python 3.13 standard library
COPY --from=python-builder /usr/local/lib/python3.13 /usr/local/lib/python3.13

# Copy Python shared library into a path musl's dynamic linker searches by default
COPY --from=python-builder /usr/local/lib/libpython3.13.so.1.0 /usr/lib/libpython3.13.so.1.0
RUN ln -sf /usr/lib/libpython3.13.so.1.0 /usr/lib/libpython3.13.so

# Expose python3 at /usr/bin so n8n's `python3 --version` check finds it
RUN ln -sf /usr/local/bin/python3 /usr/bin/python3

# Copy task-runner-python source + venv to the exact path n8n resolves at runtime:
# path.join(__dirname, '../../../@n8n/task-runner-python')
# __dirname = /usr/local/lib/node_modules/n8n/dist/task-runners
# → /usr/local/lib/node_modules/@n8n/task-runner-python
COPY --from=python-builder /n8n-src/packages/@n8n/task-runner-python \
    /usr/local/lib/node_modules/@n8n/task-runner-python

USER node
