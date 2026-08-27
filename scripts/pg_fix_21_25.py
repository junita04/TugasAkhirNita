"""
Fix query_context for chart 21 (table) and 25 (histogram).
These need empty metrics but correct columns from params.
The stored query_context from build_qc generates columns: [] instead of columns from params.
"""
import psycopg2
import json

# Chart 21: Classification Report - table viz
qc21 = {
    "datasource": {"id": 10, "type": "table"},
    "queries": [{
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": 10,
        "metrics": [],
        "filters": [],
        "columns": ["class", "precision", "recall", "f1_score", "support"]
    }],
    "form_data": {
        "all_columns": ["class", "precision", "recall", "f1_score", "support"],
        "order_desc": True,
        "row_limit": 10,
        "page_length": 10,
        "include_search": False,
        "table_timestamp_format": "smart_date",
        "show_cell_bars": True,
        "color_pn": True,
        "viz_type": "table"
    },
    "result_format": "json",
    "result_type": "full"
}

# Chart 25: Distribusi IPK Mahasiswa Aktif - histogram viz
qc25 = {
    "datasource": {"id": 5, "type": "table"},
    "queries": [{
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": 50000,
        "metrics": [],
        "filters": [{"col": "status_mahasiswa", "op": "==", "val": "AKTIF"}],
        "columns": ["ipk"]
    }],
    "form_data": {
        "all_columns_x": ["ipk"],
        "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "status_mahasiswa", "operator": "==", "comparator": "AKTIF", "clause": "WHERE"}],
        "row_limit": 50000,
        "link_length": 25,
        "x_axis_label": "IPK",
        "y_axis_label": "Jumlah Mahasiswa",
        "color_scheme": "supersetColors",
        "normalized": False,
        "viz_type": "histogram"
    },
    "result_format": "json",
    "result_type": "full"
}

conn = psycopg2.connect(host="localhost", database="superset", user="academic")
cur = conn.cursor()

cur.execute("UPDATE slices SET query_context = %s WHERE id = 21", (json.dumps(qc21),))
cur.execute("UPDATE slices SET query_context = %s WHERE id = 25", (json.dumps(qc25),))

conn.commit()
print(f"Updated charts 21 and 25 query_context")

# Verify
cur.execute("SELECT id, slice_name, length(query_context) as qc_len FROM slices WHERE id IN (21, 25)")
for row in cur.fetchall():
    print(f"  Chart {row[0]} ({row[1]}): QC len = {row[2]}")

cur.close()
conn.close()
