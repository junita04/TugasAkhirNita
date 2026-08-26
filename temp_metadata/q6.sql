SELECT
  COUNT(*) AS total,
  SUM(CASE WHEN "status mahasiswa" IS NULL THEN 1 ELSE 0 END) AS null_status,
  SUM(CASE WHEN UPPER(TRIM("status mahasiswa")) NOT IN ('AKTIF','LULUS','DIKELUARKAN','MENGUNDURKAN DIRI','LAINNYA','WAFAT') THEN 1 ELSE 0 END) AS status_unknown
FROM iceberg.bronze.data_referensi_mahasiswa;