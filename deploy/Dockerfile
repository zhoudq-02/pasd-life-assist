# Offline-capable image: core self-tests need NO third-party Python package.
# Contract: docs/08 section 4. Real hardware is deliberately NOT enabled here.
FROM python:3.11-slim

ARG EXTRAS=""
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONUTF8=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src:/app:/app/integration \
    PASD_HOME=/state \
    PASD_BACKEND=mock \
    PASD_ALLOW_REAL=0 \
    PASD_ESTOP_ACK=0

# libGL / OSMesa are only needed when the optional MuJoCo extra is installed.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      bash ca-certificates git iproute2 libgl1 libglib2.0-0 libosmesa6 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

# Optional: build with --build-arg EXTRAS=dev (or sim,robot,agent,all).
RUN if [ -n "$EXTRAS" ]; then \
      python3 -m pip install --no-cache-dir -e ".[$EXTRAS]" ; \
    fi \
 && mkdir -p /state/logs /state/runs /state/artifacts \
 && chown -R 1000:1000 /app /state

USER 1000:1000
CMD ["python3", "scripts/contract_tests.py"]
