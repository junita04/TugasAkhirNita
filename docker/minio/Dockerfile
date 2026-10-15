FROM python:3.11-slim

# Install AWS CLI and curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    pip install --no-cache-dir awscli && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY init.sh /init.sh
RUN chmod +x /init.sh

ENTRYPOINT ["/init.sh"]