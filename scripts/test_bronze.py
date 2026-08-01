from pathlib import Path

from backend.bronze.bronze import load_all_sheets_to_bronze


def main():

    load_all_sheets_to_bronze(
        Path("data/req_data_rut.xlsx")
    )


if __name__ == "__main__":
    main()