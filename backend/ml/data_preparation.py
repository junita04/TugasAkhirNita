from pyspark.ml import Pipeline
from pyspark.ml.feature import StringIndexer, VectorAssembler

from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def prepare_training_dataset():

    spark = get_spark("Machine Learning")

    logger.info("=" * 60)
    logger.info("MEMBUAT PREPARED TRAINING DATASET")
    logger.info("=" * 60)

    # =====================================================
    # Membaca Training Dataset
    # =====================================================

    df = spark.table(
        f"{ICEBERG_NAMESPACE}.feature_store.training_dataset"
    )

    logger.info(f"Rows Training Dataset : {df.count()}")

    logger.info("Distribusi Label")

    df.groupBy(
        "status_kelulusan"
    ).count().show(truncate=False)

    # =====================================================
    # String Indexer
    # =====================================================

    gender_indexer = StringIndexer(
        inputCol="jenis_kelamin",
        outputCol="jenis_kelamin_index",
        handleInvalid="keep"
    )

    label_indexer = StringIndexer(
        inputCol="status_kelulusan",
        outputCol="label",
        handleInvalid="keep"
    )

    # =====================================================
    # Vector Assembler
    # =====================================================

    assembler = VectorAssembler(
        inputCols=[
            "jenis_kelamin_index",
            "estimasi_semester",
            "ipk",
            "total_sks",
            "jumlah_mk",
            "persentase_sks"
        ],
        outputCol="features"
    )

    # =====================================================
    # Pipeline
    # =====================================================

    pipeline = Pipeline(
        stages=[
            gender_indexer,
            label_indexer,
            assembler
        ]
    )

    pipeline_model = pipeline.fit(df)

    prepared_df = pipeline_model.transform(df)

    # =====================================================
    # Feature Pipeline (gender indexer + assembler saja)
    #
    # Dipakai untuk inferensi sehingga pemetaan gender index
    # SAMA dengan saat training (StringIndexer order berbasis
    # frekuensi; mem-fit ulang pada data inferensi dapat
    # menghasilkan pemetaan yang berbeda). Disimpan di
    # Model Registry bersama model.
    # =====================================================

    feature_pipeline = Pipeline(
        stages=[
            gender_indexer,
            assembler
        ]
    )

    feature_pipeline_model = feature_pipeline.fit(df)

    # =====================================================
    # Urutan Label (indeks StringIndexer -> label)
    #
    # Diambil dari label_indexer yang sudah di-fit (stage index 1
    # pada pipeline penuh: [gender_indexer, label_indexer, assembler]).
    # =====================================================

    label_order = list(pipeline_model.stages[1].labels)

    logger.info(f"Rows Prepared Dataset : {prepared_df.count()}")
    logger.info(f"Jumlah Feature : {len(assembler.getInputCols())}")

    logger.info("=" * 60)
    logger.info("SCHEMA PREPARED DATASET")
    logger.info("=" * 60)

    prepared_df.printSchema()

    logger.info("✓ Prepared Training Dataset berhasil dibuat.")
    logger.info("=" * 60)

    return prepared_df, feature_pipeline_model, label_order
