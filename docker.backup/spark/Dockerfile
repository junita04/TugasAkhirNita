FROM apache/spark:3.5.3

USER root

# ============================================================
# Dependency jar yang dibutuhkan seluruh pipeline:
#   - Apache Iceberg runtime (Spark 3.5)
#   - PostgreSQL JDBC (serving layer)
#   - Hadoop-AWS + AWS SDK (MinIO / S3)
# ============================================================

RUN if [ -d /opt/spark ] && [ ! -e /opt/bitnami/spark ]; then \
        mkdir -p /opt/bitnami && ln -s /opt/spark /opt/bitnami/spark; \
    fi \
    && mkdir -p /opt/bitnami/spark/jars/extra

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL -o /opt/bitnami/spark/jars/extra/iceberg-spark-runtime-3.5_2.12.jar \
        https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/1.5.2/iceberg-spark-runtime-3.5_2.12-1.5.2.jar && \
    curl -fsSL -o /opt/bitnami/spark/jars/extra/postgresql.jar \
        https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.4/postgresql-42.7.4.jar && \
    curl -fsSL -o /opt/bitnami/spark/jars/extra/hadoop-aws.jar \
        https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar && \
    curl -fsSL -o /opt/bitnami/spark/jars/extra/aws-java-sdk-bundle.jar \
        https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.261/aws-java-sdk-bundle-1.12.261.jar && \
    curl -fsSL -o /opt/bitnami/spark/jars/extra/commons-pool2.jar \
        https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar

ENV SPARK_JARS_EXTRA=/opt/bitnami/spark/jars/extra

# UID 1001 harus punya entri di /etc/passwd & /etc/group. Jika tidak, Hadoop's
# UserGroupInformation -> UnixLoginModule gagal dengan
# "NullPointerException: invalid null input: name" saat Spark Master start.
RUN if ! getent passwd 1001 >/dev/null 2>&1; then \
        if ! getent group 1001 >/dev/null 2>&1; then \
            echo "sparkdl:x:1001:" >> /etc/group; \
        fi; \
        echo "sparkdl:x:1001:1001:Spark:/opt/spark:/bin/bash" >> /etc/passwd; \
    fi \
    && chown -R 1001:1001 /opt/spark

USER 1001
