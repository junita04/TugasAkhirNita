from backend.spark.session import get_spark


def main():
    spark = get_spark()

    print("=" * 50)
    print("Spark Session Berhasil Dibuat")
    print("=" * 50)

    print(f"App Name : {spark.sparkContext.appName}")
    print(f"Master   : {spark.sparkContext.master}")
    print(f"Version  : {spark.version}")

    spark.stop()


if __name__ == "__main__":
    main()