FROM apache/hive:3.1.3

USER root

# Tool pendukung download dependency
RUN apt-get update && apt-get install -y --no-install-recommends curl netcat-openbsd && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Dependency: Postgres JDBC untuk backend metadata
# Hapus driver lama (tidak mendukung SCRAM-SHA-256 PG16)
RUN rm -f /opt/hive/lib/postgresql-*.jar && \
    curl -fsSL -o /opt/hive/lib/postgresql.jar \
        https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.4/postgresql-42.7.4.jar

# Hive Metastore must understand the warehouse URI when Iceberg creates
# namespaces/tables. Use the Hadoop-AWS version matching Hive's Hadoop 3.1.x.
RUN curl -fsSL -o /opt/hive/lib/hadoop-aws.jar \
        https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.1.0/hadoop-aws-3.1.0.jar && \
    curl -fsSL -o /opt/hive/lib/aws-java-sdk-bundle.jar \
        https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.11.375/aws-java-sdk-bundle-1.11.375.jar

COPY hive-site.xml /opt/hive/conf/hive-site.xml

# Entrypoint bawaan image memakai DB_DRIVER (default derby).
# Arahkan ke PostgreSQL dan jalankan service metastore.
# IS_RESUME=true -> lewati inisialisasi schema ulang
ENV DB_DRIVER=postgres \
    SERVICE_NAME=metastore \
    METASTORE_PORT=9083 \
    IS_RESUME=true

USER hive

EXPOSE 9083
