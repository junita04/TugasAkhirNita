#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Inisialisasi bucket MinIO untuk Data Lakehouse
# ============================================================

echo "Waiting for MinIO..."
until mc alias set local http://minio:9000 "${MINIO_ROOT_USER}" "${MINIO_ROOT_PASSWORD}" >/dev/null 2>&1; do
    sleep 2
done

echo "Configuring MinIO client..."

BUCKETS=(
    "${MINIO_BUCKET_WAREHOUSE}"
    "${MINIO_BUCKET_RAW}"
    "${MINIO_BUCKET_MODELS}"
    "${MINIO_BUCKET_LOGS}"
)

for bucket in "${BUCKETS[@]}"; do
    if mc ls "local/${bucket}" >/dev/null 2>&1; then
        echo "Bucket already exists: ${bucket}"
    else
        echo "Creating bucket: ${bucket}"
        mc mb "local/${bucket}"
    fi
done

# Seed the original project dataset into the raw zone. This is intentionally
# idempotent so restarting Compose does not create duplicate objects.
if [[ -f /seed-data/req_data_rut.xlsx ]]; then
    echo "Uploading original dataset to raw bucket..."
    mc cp /seed-data/req_data_rut.xlsx "local/${MINIO_BUCKET_RAW}/req_data_rut.xlsx"
else
    echo "Original dataset not found at /seed-data/req_data_rut.xlsx"
fi

echo "Buckets created:"
mc ls local
