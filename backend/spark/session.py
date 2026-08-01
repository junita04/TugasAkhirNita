from pyspark.sql import SparkSession

from backend.config.settings import (
    APP_NAME,
    MASTER,
    ICEBERG_DIR,
    SPARK_EVENT_LOG,
    SPARK_EVENT_LOG_DIR,
)


def get_spark(app_name: str = APP_NAME) -> SparkSession:
    """
    Membuat SparkSession yang digunakan
    di seluruh project.
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

    spark = (
        SparkSession.builder
        .appName(app_name)
        .master(MASTER)

        # =====================================================
        # Memory Configuration
        # =====================================================

        .config("spark.driver.memory", "4g")
        .config("spark.executor.memory", "4g")
        .config("spark.driver.maxResultSize", "2g")

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
                "com.crealytics:spark-excel_2.12:3.5.1_0.20.4"
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

        # =====================================================
        # Driver
        # =====================================================

        .config(
            "spark.driver.host",
            "127.0.0.1"
        )

        .config(
            "spark.driver.bindAddress",
            "127.0.0.1"
        )

        # =====================================================
        # Iceberg Catalog
        # =====================================================

        .config(
            "spark.sql.catalog.local",
            "org.apache.iceberg.spark.SparkCatalog"
        )

        .config(
            "spark.sql.catalog.local.type",
            "hadoop"
        )

        .config(
            "spark.sql.catalog.local.warehouse",
            str(ICEBERG_DIR)
        )

        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    print("=" * 60)
    print(f"Spark App Name : {spark.sparkContext.appName}")
    print("=" * 60)

    return spark