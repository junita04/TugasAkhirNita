from backend.utils.logger import get_logger

logger = get_logger(__name__)

logger.info("Logger berhasil dibuat")
logger.warning("Ini contoh warning")
logger.error("Ini contoh error")

# python -m scripts.test_logger