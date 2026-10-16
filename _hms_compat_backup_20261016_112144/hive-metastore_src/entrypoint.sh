#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Ganti token ${env:VAR} di hive-site.xml dengan nilai aktual
# environment sebelum metastore start. Hadoop/Hive di image
# apache/hive:3.1.3 TIDAK melakukan ekspansi otomatis, sehingga
# nilai yang dipakai kredensial menjadi literal token.
# ============================================================

CONF_DIR=/opt/hive/conf
SITE="$CONF_DIR/hive-site.xml"
TMP="$CONF_DIR/hive-site.xml.generated"

vars=(POSTGRES_HIVE_USER POSTGRES_HIVE_PASSWORD MINIO_ROOT_USER MINIO_ROOT_PASSWORD)

: > "$TMP"
while IFS= read -r line; do
    for var in "${vars[@]}"; do
        value="${!var:-}"
        if [ -n "$value" ]; then
            line="${line//\$\{env:${var}\}/$value}"
        fi
    done
    printf '%s\n' "$line" >> "$TMP"
done < "$SITE"

mv -f "$TMP" "$SITE"

exec /entrypoint.sh "$@"