SELECT
  SUM(CASE WHEN "total sks" IS NOT NULL AND CAST("total sks" AS INT) < 0 THEN 1 ELSE 0 END) AS total_sks_negatif,
  SUM(CASE WHEN "jumlah mk" IS NOT NULL AND CAST("jumlah mk" AS INT) < 0 THEN 1 ELSE 0 END) AS jumlah_mk_negatif
FROM iceberg.bronze.data_referensi_mahasiswa;