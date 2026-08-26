SELECT
  COUNT(*) AS total,
  COUNT(DISTINCT "id_mhs") AS unique_ids,
  COUNT(*) - COUNT(DISTINCT "id_mhs") AS duplicate_ids
FROM iceberg.bronze.data_referensi_mahasiswa;
