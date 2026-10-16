# ============================================================
# STAGING ONLY - DO NOT APPLY WITHOUT EXPLICIT APPROVAL
# ------------------------------------------------------------
# Usulan Dockerfile HMS 3.1.3 (pengganti docker/hive-metastore/Dockerfile
# yang saat ini memakai apache/hive:standalone-metastore-4.2.1).
#
# Alasan: Spark 3.5.3 memakai klien Hive 2.3.9 yang memanggil method thrift
# get_table / get_table_objects_by_name. Hive 4.x menghapus method tersebut
# (HIVE-26537) sehingga Spark -> HMS 4.2.1 gagal.
#
# File ini TIDAK dipakai oleh docker-compose.yml (yang memakai context
# ./docker/hive-metastore). Menyalin langsung ke sana = perubahan produksi
# dan butuh persetujuan eksplisit.
# ============================================================
FROM apache/hive:3.1.3

USER root

# Tool pendukung (sama seperti image 4.2.1 versi aktif)
RUN apt-get update && apt-get install -y --no-install-recommends curl netcat-openbsd && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Driver Postgres 42.7.4 (menggantikan driver lama yang gagal di PG16: am.amcanorder)
RUN rm -f /opt/hive/lib/postgresql-*.jar && \
    curl -fsSL -o /opt/hive/lib/postgresql.jar \
        https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.4/postgresql-42.7.4.jar

# Hadoop-AWS yang cocok dengan Hadoop 3.1.x milik image Hive 3.1.3
RUN curl -fsSL -o /opt/hive/lib/hadoop-aws.jar \
        https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.1.0/hadoop-aws-3.1.0.jar && \
    curl -fsSL -o /opt/hive/lib/aws-java-sdk-bundle.jar \
        https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.11.375/aws-java-sdk-bundle-1.11.375.jar

# Symlink lokasi warehouse Iceberg lokal (D:/TA/...) agar HMS dapat memvalidasi
# direktori lokasi tabel saat register_table/create_table (Trino memakai path ini).
# Target /data/iceberg diisi bind-mount ./iceberg:/data/iceberg (ro) dari compose.
RUN mkdir -p /D:/TA/TugasAkhirNita && \
    ln -sfn /data/iceberg /D:/TA/TugasAkhirNita/iceberg

COPY hive-site.xml /opt/hive/conf/hive-site.xml
COPY entrypoint.sh /opt/hive/bin/entrypoint-wrapper.sh
RUN chmod +x /opt/hive/bin/entrypoint-wrapper.sh

# Wrapper melakukan substitusi ${env:VAR} di hive-site.xml karena
# image apache/hive:3.1.3 tidak mengekspansi-nya secara otomatis.
ENTRYPOINT ["/opt/hive/bin/entrypoint-wrapper.sh"]

# IS_RESUME=false HANYA pada run pertama (inisialisasi skema 3.1.0 di DB baru
# `metastore313`). Setelah sukses, kembalikan ke true.
ENV DB_DRIVER=postgres \
    SERVICE_NAME=metastore \
    METASTORE_PORT=9083 \
    IS_RESUME=true

USER hive

EXPOSE 9083
