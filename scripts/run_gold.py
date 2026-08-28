"""Run Gold layer processing."""
import sys
sys.path.insert(0, "/opt/airflow")

from backend.gold.gold import process_gold

result = process_gold()
print(f"\nGold completed successfully.")
