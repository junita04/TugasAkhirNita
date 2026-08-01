from backend.gold.gold_mahasiswa import process_gold_mahasiswa
from backend.gold.gold_prodi import process_gold_program_studi
from backend.gold.gold_kurikulum import process_gold_kurikulum

from backend.utils.logger import get_logger

logger = get_logger(__name__)


def process_gold():

    logger.info("=" * 60)
    logger.info("Memulai Proses Gold Layer")
    logger.info("=" * 60)

    process_gold_mahasiswa()

    process_gold_program_studi()

    process_gold_kurikulum()

    logger.info("=" * 60)
    logger.info("Seluruh Gold Layer berhasil dibuat.")
    logger.info("=" * 60)