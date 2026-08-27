import json

qc21 = {"datasource": {"id": 10, "type": "table"}, "queries": [{"time_range": "No filter", "granularity_sqla": None, "row_limit": 10, "metrics": [], "filters": [], "columns": ["class", "precision", "recall", "f1_score", "support"]}], "form_data": {"all_columns": ["class", "precision", "recall", "f1_score", "support"], "order_desc": True, "row_limit": 10, "page_length": 10, "include_search": False, "table_timestamp_format": "smart_date", "show_cell_bars": True, "color_pn": True}, "result_format": "json", "result_type": "full"}

qc25 = {"datasource": {"id": 5, "type": "table"}, "queries": [{"time_range": "No filter", "granularity_sqla": None, "row_limit": 50000, "metrics": [], "filters": [{"col": "status_mahasiswa", "op": "==", "val": "AKTIF"}], "columns": ["ipk"]}], "form_data": {"all_columns_x": ["ipk"], "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "status_mahasiswa", "operator": "==", "comparator": "AKTIF", "clause": "WHERE"}], "row_limit": 50000, "link_length": 25, "x_axis_label": "IPK", "y_axis_label": "Jumlah Mahasiswa", "color_scheme": "supersetColors", "normalized": False}, "result_format": "json", "result_type": "full"}

sql21 = "UPDATE slices SET query_context = '" + json.dumps(qc21).replace("'", "''") + "' WHERE id = 21;"
sql25 = "UPDATE slices SET query_context = '" + json.dumps(qc25).replace("'", "''") + "' WHERE id = 25;"

with open("D:/TA/TugasAkhirNita/scripts/update_qc.sql", "w") as f:
    f.write(sql21 + "\n")
    f.write(sql25 + "\n")

print("SQL written")
