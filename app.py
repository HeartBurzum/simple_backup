import logging
import sys

from backup import Backup
from config import Config
from encryption import Encrypt

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    config = Config()

    if config.encryption_enabled:
        encrypt = Encrypt(config)
        encrypt.check_keyring()
        if not encrypt.fingerprint_in_keyring():
            logger.critical("Encryption check failure.")
            sys.exit(1)

    backup = Backup(config)
    if config.encryption_enabled:
        encrypt.start_encryption(backup.tar_files)
