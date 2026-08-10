import os

from pyspark.sql import SparkSession

from backend.config.settings import (
    APP_NAME,
    MASTER,
    SPARK_EVENT_LOG,
    SPARK_EVENT_LOG_DIR,
    SPARK_MODE,
    ICEBERG_CATALOG,
    ICEBERG_NAMESPACE,
    ICEBERG_WAREHOUSE,
    S3_ACCESS_KEY,
    S3_SECRET_KEY,
    S3_ENDPOINT,
    S3_PATH_STYLE_ACCESS,
    HIVE_METASTORE_URI,
)


SPARK_LOCAL_DIR = os.getenv("SPARK_LOCAL_DIRS", "spark-tmp")


def _iceberg_configs(spark_builder):
    """
    Mengonfigurasi Iceberg catalog berdasarkan ICEBERG_CATALOG:
      - 'local'  : warehouse filesystem (jalankan dari mesin lokal)
      - 'hive'   : Hive Metastore + warehouse di MinIO (cluster)
    """

    if ICEBERG_CATALOG != "local":
        return (
            spark_builder
            .config(
                f"spark.sql.catalog.{ICEBERG_CATALOG}",
                "org.apache.iceberg.spark.SparkCatalog"
            )
            .config(f"spark.sql.catalog.{ICEBERG_CATALOG}.type", "hive")
            .config(f"spark.sql.catalog.{ICEBERG_CATALOG}.uri", HIVE_METASTORE_URI)
            .config(
                f"spark.sql.catalog.{ICEBERG_CATALOG}.warehouse",
                ICEBERG_WAREHOUSE,
            )
            .config(
                f"spark.sql.catalog.{ICEBERG_CATALOG}.cache-enabled",
                "false",
            )
            # S3 (MinIO)
            .config("spark.hadoop.fs.s3a.endpoint", S3_ENDPOINT)
            .config("spark.hadoop.fs.s3a.access.key", S3_ACCESS_KEY)
            .config("spark.hadoop.fs.s3a.secret.key", S3_SECRET_KEY)
            .config("spark.hadoop.fs.s3a.path.style.access", str(S3_PATH_STYLE_ACCESS).lower())
            .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
            .config("spark.hadoop.fs.s3a.fast.upload", "true")
            .config("spark.hadoop.fs.s3a.fast.upload.buffer", "bytebuffer")
            .config("spark.hadoop.fs.s3a.buffer.dir", SPARK_LOCAL_DIR)
        )

    return (
        spark_builder
        .config(
            "spark.sql.catalog.local",
            "org.apache.iceberg.spark.SparkCatalog"
        )
        .config("spark.sql.catalog.local.type", "hadoop")
        .config("spark.sql.catalog.local.warehouse", ICEBERG_WAREHOUSE)
    )


def get_spark(app_name: str = APP_NAME) -> SparkSession:
    """
    Membuat SparkSession yang digunakan di seluruh project.
    Mode 'local' (default) memakai core CPU mesin.
    Mode 'cluster' memakai Spark Master dari Docker.
    """

    # ==========================================
    # Tutup SparkSession lama jika masih ada
    # ==========================================

    active_session = SparkSession.getActiveSession()

    if active_session is not None:
        active_session.stop()

    # ==========================================
    # Membuat SparkSession baru
    # ==========================================

    builder = (
        SparkSession.builder
        .appName(app_name)
        .master(MASTER)

        # =====================================================
        # Memory Configuration
        # =====================================================

        .config("spark.driver.memory", "4g")
        .config("spark.executor.memory", "4g")
        .config("spark.driver.maxResultSize", "2g")
        .config("spark.local.dir", SPARK_LOCAL_DIR)

        # =====================================================
        # Performance
        # =====================================================

        .config("spark.sql.shuffle.partitions", "8")

        # =====================================================
        # Download dependency otomatis
        # =====================================================

        .config(
            "spark.jars.packages",
            ",".join([
                "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.2",
                "com.crealytics:spark-excel_2.12:3.5.1_0.20.4",
                "org.postgresql:postgresql:42.7.4",
                "org.apache.hadoop:hadoop-aws:3.3.4",
                "com.amazonaws:aws-java-sdk-bundle:1.12.261",
            ])
        )

        # =====================================================
        # Event Log
        # =====================================================

        .config(
            "spark.eventLog.enabled",
            str(SPARK_EVENT_LOG).lower()
        )

        .config(
            "spark.eventLog.dir",
            SPARK_EVENT_LOG_DIR
        )
    )

    # =====================================================
    # Driver host (dibutuhkan terutama pada mode local)
    # =====================================================

    if SPARK_MODE == "local":
        builder = (
            builder
            .config("spark.driver.host", "127.0.0.1")
            .config("spark.driver.bindAddress", "127.0.0.1")
        )

    # =====================================================
    # Iceberg Catalog
    # =====================================================

    builder = _iceberg_configs(builder)

    spark = builder.getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    # HiveCatalog does not create namespaces implicitly. Create every
    # namespace used by the Bronze/Silver/Gold and feature-store stages.
    for namespace in ("bronze", "silver", "gold", "feature_store"):
        spark.sql(
            f"CREATE NAMESPACE IF NOT EXISTS {ICEBERG_NAMESPACE}.{namespace}"
        )

    print("=" * 60)
    print(f"Spark App Name : {spark.sparkContext.appName}")
    print(f"Spark Mode     : {SPARK_MODE}")
    print(f"Iceberg Catalog: {ICEBERG_CATALOG}")
    print("=" * 60)

    return spark
