#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Inisialisasi bucket MinIO untuk Data Lakehouse menggunakan AWS CLI
# ============================================================

export AWS_ACCESS_KEY_ID="${MINIO_ROOT_USER}"
export AWS_SECRET_ACCESS_KEY="${MINIO_ROOT_PASSWORD}"
export AWS_DEFAULT_REGION="${S3_REGION:-us-east-1}"
ENDPOINT_URL="http://minio:9000"

echo "Waiting for MinIO..."
until curl -sf "${ENDPOINT_URL}/minio/health/live" >/dev/null 2>&1; do
    sleep 2
done

echo "Configuring AWS CLI..."
aws configure set default.s3.signature_version s3v4

BUCKETS=(
    "${MINIO_BUCKET_WAREHOUSE}"
    "${MINIO_BUCKET_RAW}"
    "${MINIO_BUCKET_MODELS}"
    "${MINIO_BUCKET_LOGS}"
)

for bucket in "${BUCKETS[@]}"; do
    if aws --endpoint-url="${ENDPOINT_URL}" s3 ls "s3://${bucket}" >/dev/null 2>&1; then
        echo "Bucket already exists: ${bucket}"
    else
        echo "Creating bucket: ${bucket}"
        aws --endpoint-url="${ENDPOINT_URL}" s3 mb "s3://${bucket}"
    fi
done

# Seed the original project dataset into the raw zone
if [[ -f /seed-data/req_data_rut.xlsx ]]; then
    echo "Uploading original dataset to raw bucket..."
    aws --endpoint-url="${ENDPOINT_URL}" s3 cp /seed-data/req_data_rut.xlsx "s3://${MINIO_BUCKET_RAW}/req_data_rut.xlsx"
else
    echo "Original dataset not found at /seed-data/req_data_rut.xlsx"
fi

# Seed the NEW dataset
if [[ -f "/seed-data/(asli)req_data_rut (1).xlsx" ]]; then
    echo "Uploading NEW dataset to raw bucket..."
    aws --endpoint-url="${ENDPOINT_URL}" s3 cp "/seed-data/(asli)req_data_rut (1).xlsx" "s3://${MINIO_BUCKET_RAW}/(asli)req_data_rut (1).xlsx"
else
    echo "NEW dataset not found at /seed-data/(asli)req_data_rut (1).xlsx"
fi

echo "Buckets created:"
aws --endpoint-url="${ENDPOINT_URL}" s3 ls