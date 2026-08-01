from pathlib import Path

from backend.utils.excel_utils import read_excel

# Ganti dengan file Excel yang nanti akan dipakai
file = Path("data/req_data_rut.xlsx")

if file.exists():
    df = read_excel(file)
    print(df.head())
else:
    print("File Excel belum ada, test dilewati.")