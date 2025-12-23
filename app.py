import logging

from backup import Backup
from config import Config

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    config = Config()

    backup = Backup(config)
