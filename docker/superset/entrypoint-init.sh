#!/usr/bin/env bash
set -euo pipefail

superset db upgrade

superset init
python /app/docker/create_admin.py
python /app/docker/register_datasets.py
