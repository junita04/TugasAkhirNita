import logging


def get_logger(name: str) -> logging.Logger:
    """
    Membuat logger untuk seluruh project.
    """

    logger = logging.getLogger(name)

    if not logger.hasHandlers():

        logger.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "[%(levelname)s] %(asctime)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    return logger