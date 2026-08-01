from backend.spark.session import get_spark


def show_dataset_info(spark, table_name):

    print("\n" + "=" * 80)
    print(f"DATASET : {table_name}")
    print("=" * 80)

    df = spark.table(table_name)

    # =====================================================
    # Jumlah Data
    # =====================================================

    print(f"\nJumlah Data   : {df.count()}")
    print(f"Jumlah Kolom  : {len(df.columns)}")

    # =====================================================
    # Nama Kolom
    # =====================================================

    print("\nDaftar Kolom")

    for i, column in enumerate(df.columns, start=1):
        print(f"{i}. {column}")

    # =====================================================
    # Schema
    # =====================================================

    print("\nSchema")

    df.printSchema()

    # =====================================================
    # Sample Data
    # =====================================================

    print("\n5 Data Pertama")

    df.show(5, truncate=False)

    # =====================================================
    # Missing Value
    # =====================================================

    print("\nJumlah Missing Value")

    for column in df.columns:

        missing = df.filter(df[column].isNull()).count()

        print(f"{column:<25}: {missing}")

    # =====================================================
    # Statistik Numerik
    # =====================================================

    print("\nStatistik Data Numerik")

    numeric_columns = [

        "estimasi_semester",
        "ipk",
        "total_sks",
        "jumlah_mk",
        "persentase_sks"

    ]

    available_columns = [
        col for col in numeric_columns if col in df.columns
    ]

    if available_columns:

        df.select(*available_columns).describe().show()

    # =====================================================
    # Distribusi Label
    # =====================================================

    if "status_kelulusan" in df.columns:

        print("\nDistribusi Status Kelulusan")

        df.groupBy("status_kelulusan") \
            .count() \
            .show()


def main():

    spark = get_spark("Feature Store Validation")

    show_dataset_info(
        spark,
        "local.feature_store.training_dataset"
    )

    show_dataset_info(
        spark,
        "local.feature_store.inference_dataset"
    )

    spark.stop()


if __name__ == "__main__":
    main()