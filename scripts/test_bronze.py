from backend.bronze.bronze import load_all_sheets_to_bronze
from backend.config.settings import DATA_DIR


def main():

    load_all_sheets_to_bronze(
        DATA_DIR / "req_data_rut.xlsx"
    )


if __name__ == "__main__":
    main()