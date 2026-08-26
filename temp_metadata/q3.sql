SELECT
  COUNT(*) AS keluar_sebelum_masuk
FROM iceberg.bronze.data_referensi_mahasiswa
WHERE "tanggal masuk" IS NOT NULL
  AND "tanggal keluar" IS NOT NULL
  AND CAST("tanggal keluar" AS DATE) < CAST("tanggal masuk" AS DATE);
