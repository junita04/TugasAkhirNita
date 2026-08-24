import os
import sys

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
    POSTGRES_ENABLED,
)


SPARK_LOCAL_DIR = os.getenv("SPARK_LOCAL_DIRS", "spark-tmp")

# =====================================================
# Worker Python (penting di Windows)
#
# Tanpa PYSPARK_PYTHON, PySpark memanggil interpreter 'python' apa adanya
# saat worker subprocess membuat Python UDF. Di Windows hal ini rawan
# gagal ('Python worker failed to connect back' / 'Accept timed out').
# Paksa memakai interpreter venv yang sedang berjalan.
# =====================================================

os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)


def _iceberg_configs(spark_builder):
    """
    Mengonfigurasi Iceberg catalog berdasarkan ICEBERG_CATALOG:
      - 'local'  : Hadoop catalog, warehouse di filesystem lokal
      - 'iceberg': Hadoop catalog, warehouse di MinIO (s3a://)
    """

    if ICEBERG_CATALOG != "local":
        return (
            spark_builder
            .config(
                f"spark.sql.catalog.{ICEBERG_CATALOG}",
                "org.apache.iceberg.spark.SparkCatalog"
            )
            .config(f"spark.sql.catalog.{ICEBERG_CATALOG}.type", "hadoop")
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
    # Reuse SparkSession aktif jika masih ada
    #
    # Setiap layer (bronze/silver/gold/feature store) memanggil get_spark().
    # Memaksa stop + create ulang pada tiap panggilan membuat JVM restart
    # berkali-kali dan terbukti rawan hang/connection-reset di Windows.
    # Session dibuat SEKALI lalu dipakai bersama sampai pipeline selesai.
    # ==========================================

    active_session = SparkSession.getActiveSession()

    if active_session is not None:
        return active_session

    # =====================================================
    # Dependency jar (jar lokal atau download otomatis via Ivy)
    #
    # Jika SPARK_JARS_DIR berisi jar (di-bake ke image / bind mount),
    # pakai spark.jars (tanpa resolusi Ivy saat runtime).
    # Jika tidak ada, fallback ke spark.jars.packages (download otomatis).
    # =====================================================

    jars_dir = os.getenv("SPARK_JARS_DIR", "/opt/airflow/jars")

    if os.path.isdir(jars_dir) and any(
        f.endswith(".jar") for f in os.listdir(jars_dir)
    ):
        spark_jars = ",".join(
            os.path.join(jars_dir, f)
            for f in sorted(os.listdir(jars_dir))
            if f.endswith(".jar")
        )
        packages = []
    else:
        spark_jars = None
        packages = [
            "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.2",
            "com.crealytics:spark-excel_2.12:3.5.1_0.20.4",
        ]

        if POSTGRES_ENABLED:
            packages.append("org.postgresql:postgresql:42.7.4")

        if ICEBERG_CATALOG != "local":
            packages.append("org.apache.hadoop:hadoop-aws:3.3.4")
            packages.append("com.amazonaws:aws-java-sdk-bundle:1.12.261")

    # =====================================================
    # Membuat SparkSession baru
    # =====================================================

    builder = (
        SparkSession.builder
        .appName(app_name)
        .master(MASTER)

        # =====================================================
        # Memory Configuration
        # =====================================================

        .config(
            "spark.driver.memory",
            os.getenv("SPARK_DRIVER_MEMORY", "1g" if SPARK_MODE == "cluster" else "4g"),
        )
        .config("spark.executor.memory", os.getenv("SPARK_EXECUTOR_MEMORY", "1g"))
        .config("spark.executor.cores", os.getenv("SPARK_EXECUTOR_CORES", "4"))
        .config("spark.driver.maxResultSize", "2g")
        .config("spark.local.dir", SPARK_LOCAL_DIR)

        # =====================================================
        # Iceberg SQL extensions
        # =====================================================

        .config(
            "spark.sql.extensions",
            "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions"
        )

        # =====================================================
        # Performance
        # =====================================================

        .config("spark.sql.shuffle.partitions", "8")
    )

    # =====================================================
    # Dependency (jar lokal tanpa Ivy, atau packages Ivy)
    #
    # extraClassPath: driver & executor membaca jar dari filesystem
    # masing-masing (folder yang di-mount identik), sehingga tidak ada
    # lagi transfer ratusan MB via Spark jar-server setiap session.
    # =====================================================

    if spark_jars:
        builder = (
            builder
            .config("spark.driver.extraClassPath", f"{jars_dir}/*")
            .config("spark.executor.extraClassPath", f"{jars_dir}/*")
        )
    else:
        builder = builder.config(
            "spark.jars.packages",
            ",".join(packages),
        )

    # =====================================================
    # Event Log
    # =====================================================

    builder = (
        builder
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
