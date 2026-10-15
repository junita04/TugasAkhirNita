FROM apache/hive:standalone-metastore-4.2.1

USER root

# Tool pendukung download dependency (already available in base image)
# RUN apt-get update && apt-get install -y --no-install-recommends curl netcat-openbsd && \
#     apt-get clean && rm -rf /var/lib/apt/lists/*

# Dependency: Postgres JDBC untuk backend metadata
# Hapus driver lama (tidak mendukung SCRAM-SHA-256 PG16)
RUN rm -f /opt/hive/lib/postgresql-*.jar && \
    curl -fsSL -o /opt/hive/lib/postgresql.jar \
        https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.4/postgresql-42.7.4.jar

# Hive Metastore must understand the warehouse URI when Iceberg creates
# namespaces/tables. Use Hadoop-AWS version matching Spark's 3.3.4 for compatibility.
RUN rm -f /opt/hive/lib/hadoop-aws-*.jar && \
    rm -f /opt/hive/lib/aws-java-sdk-bundle-*.jar && \
    curl -fsSL -o /opt/hive/lib/hadoop-aws.jar \
        https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar && \
    curl -fsSL -o /opt/hive/lib/aws-java-sdk-bundle.jar \
        https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.261/aws-java-sdk-bundle-1.12.261.jar && \
    curl -fsSL -o /opt/hive/lib/hadoop-yarn-common.jar \
        https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-yarn-common/3.3.4/hadoop-yarn-common-3.3.4.jar

# Symlink lokasi warehouse Iceberg lokal (D:/TA/...) agar HMS dapat memvalidasi
# direktori lokasi tabel saat register_table/create_table (Trino memakai path ini).
RUN mkdir -p /D:/TA/TugasAkhirNita && \
    ln -sfn /data/iceberg /D:/TA/TugasAkhirNita/iceberg

COPY hive-site.xml /opt/hive/conf/hive-site.xml
COPY entrypoint.sh /opt/hive/bin/entrypoint-wrapper.sh
RUN chmod +x /opt/hive/bin/entrypoint-wrapper.sh

# Wrapper melakukan substitusi ${env:VAR} di hive-site.xml karena
# Hadoop/Hive image apache/hive:standalone-metastore-4.2.1 tidak mengekspansi-nya secara otomatis.
ENTRYPOINT ["/opt/hive/bin/entrypoint-wrapper.sh"]

# Entrypoint bawaan image memakai DB_DRIVER (default derby).
# Arahkan ke PostgreSQL dan jalankan service metastore.
# IS_RESUME=true -> lewati inisialisasi schema ulang
ENV DB_DRIVER=postgres \
    SERVICE_NAME=metastore \
    METASTORE_PORT=9083 \
    IS_RESUME=true

USER hive

EXPOSE 9083