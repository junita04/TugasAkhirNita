SELECT
  SUM(CASE WHEN "ipk" IS NULL THEN 1 ELSE 0 END) AS ipk_null,
  SUM(CASE WHEN "ipk" IS NOT NULL AND (CAST("ipk" AS DOUBLE) < 0 OR CAST("ipk" AS DOUBLE) > 4) THEN 1 ELSE 0 END) AS ipk_out_of_range
FROM iceberg.bronze.data_referensi_mahasiswa;