SELECT id, dashboard_id, slice_id FROM dashboard_slices WHERE dashboard_id = 3;
-- Expected: 0 rows (THIS IS THE BUG)

-- Also check other dashboards
SELECT dashboard_id, COUNT(*) as chart_count FROM dashboard_slices GROUP BY dashboard_id;
