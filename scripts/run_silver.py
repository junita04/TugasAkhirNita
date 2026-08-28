"""Run Silver layer processing."""
import sys
sys.path.insert(0, "/opt/airflow")

from backend.silver.silver import process_all_tables

reports = process_all_tables()
print(f"\nSilver completed: {len(reports)} tables processed.")
