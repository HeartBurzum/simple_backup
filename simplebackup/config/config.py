import datetime
import logging
import os
import sys
from typing import Union

from simplebackup.encryption.encryption import Encrypt

log_level = logging.DEBUG
log_format = "[%(asctime)s][%(levelname)s][%(module)s] %(message)s"
logging.basicConfig(level=log_level, format=log_format)
logger = logging.getLogger(name=__name__)


class Config:
    def __init__(self):
        """
        Environment Variables:
        SIMPLE_BACKUP_PATH
        SIMPLE_BACKUP_DATA_DIR
        SIMPLE_BACKUP_NUMBER_COPIES
        SIMPLE_BACKUP_ENCRYPTION_ENABLE
        SIMPLE_BACKUP_ENCRYPTION_FINGERPRINTS
        SIMPLE_BACKUP_ENCRYPTION_PUBLIC_KEY_DIR
        SIMPLE_BACKUP_ENCRYPTION_REMOVE_UNENCRYPTED
        """
        self.timestamp = datetime.datetime.now(tz=datetime.UTC).strftime(
            "%Y%m%d-%H%M%S"
        )
        logger.info(f"Started backups at {self.timestamp}")

        self.data_dir = os.getenv("SIMPLE_BACKUP_DATA_DIR", None)
        if self.data_dir == None:
            self.data_dir = "/var/lib/simple_backup"
            logger.warning(
                f"SIMPLE_BACKUP_DATA_DIR environment variable not set. Defaulting to {self.data_dir}"
            )
        logger.info(f"Simple Backup data directory is {self.data_dir}")

        try:
            os.makedirs(self.data_dir, mode=0o600)
            logger.info(f"Created directory {self.data_dir}")
        except FileExistsError:
            pass

        if not os.access(self.data_dir, os.W_OK):
            logger.critical(f"Unable to write to {self.data_dir=}. Exiting...")
            sys.exit(1)

        self.backup_path_env_str = os.getenv(key="SIMPLE_BACKUP_PATH")
        if not self.backup_path_env_str:
            logger.critical("SIMPLE_BACKUP_PATH was unset, exiting...")
            sys.exit(1)

        self.backup_path_list = self.__split_backup_path()

        self.num_copies_str: str = os.getenv("SIMPLE_BACKUP_NUMBER_COPIES", "0")
        try:
            self.num_copies = int(self.num_copies_str)
        except ValueError:
            logger.critical(
                f"SIMPLE_BACKUP_NUMBER_COPIES environment variable needs to be a number. exiting..."
            )
            sys.exit(1)

        self.encryption_enabled = self.__get_encryption_env()
        if self.encryption_enabled:
            self.fingerprints = self.__get_key_fingerprints()
            self.key_directory = self.__get_public_key_dir()
            self.encryptor = Encrypt(self.fingerprints, self.key_directory)
            logger.debug("checking encryptor keyring")
            self.encryptor.check_keyring()
            logger.debug("finished encryptor keyring check")

    def __get_encryption_env(self) -> bool:
        enabled = False
        value: Union[str, bool] = os.getenv("SIMPLE_BACKUP_ENCRYPTION_ENABLE", enabled)
        if not value:
            logger.info("SIMPLE_BACKUP_ENCRYPTION_ENABLE env var not set")
        if type(value) == str:
            if value.lower() in ("true", "1"):
                enabled = True
            else:
                enabled = False

        logger.info(f"Backup encryption enabled: {enabled}")
        return enabled

    def __get_key_fingerprints(self) -> list[str]:
        fingerprints: Union[None, str] = os.getenv(
            "SIMPLE_BACKUP_ENCRYPTION_FINGERPRINTS", None
        )
        if not fingerprints:
            logger.critical(
                "Encryption was enabled, but no fingerprints found, check SIMPLE_BACKUP_ENCRYPTION_FINGERPRINTS or disable SIMPLE_BACKUP_ENCRYPTION_ENABLE, exiting with errors..."
            )
            sys.exit(1)

        if "," in fingerprints:
            fingerprint_list = fingerprints.split(",")
            return fingerprint_list
        else:
            return [fingerprints]

    def __get_public_key_dir(self) -> str:
        key_dir = os.getenv("SIMPLE_BACKUP_ENCRYPTION_PUBLIC_KEY_DIR", None)
        if not key_dir:
            logger.warning(
                "No SIMPLE_BACKUP_ENCRYPTION_PUBLIC_KEY_DIR set, this is not an issue if you have already imported the public keys required for encryption."
            )
            return ""
        else:
            return key_dir

    def __split_backup_path(self) -> list[str]:
        logger.debug(f"Paths set to be backed up: {self.backup_path_env_str}")
        path_list = self.backup_path_env_str.split(":")
        if not path_list:
            logger.critical(
                "Unable to create a list of paths from BACKUP_PATH env variable. Please check the syntax of BACKUP_PATH..."
            )
            sys.exit(1)
        return path_list
