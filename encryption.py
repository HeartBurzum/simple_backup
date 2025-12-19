import logging
import sys

import gnupg

from config import Config

logger = logging.getLogger(__name__)


class Encrypt:
    def __init__(self, config: Config):
        self.gpg = gnupg.GPG()
        self.recipients = config.fingerprints
        self.public_key_dir = config.key_directory
        self.public_key_dir_filelist = config.key_files
        self.keyring_ok = False

    def start_encryption(self, files: list[str]):
        for file in files:
            self.encrypt_file(file, f"{file}.asc")

    def check_keyring(self):
        if not self.fingerprint_in_keyring():
            logger.info(
                "No matching public key has been imported for supplied fingerprints."
            )
            if not self.public_key_dir_filelist:
                # we can't do anything, need to raise an error
                logger.error(
                    "No keyfiles found in public key directory, unable to complete encryption... Exiting with errors."
                )
                sys.exit(1)
            else:
                # read the keys from the public key directory
                # and check if the fingerprints of any key files
                # matches the recipients, if so, import the key to the keyring
                for file in self.public_key_dir_filelist:
                    logger.error(file)
                    with open(f"{self.public_key_dir}/{file}", "r") as key_file:
                        text = key_file.read()
                    keys = self.gpg.scan_keys_mem(text)
                    if self.recipients in keys.fingerprints:
                        result = self.gpg.import_keys(text)
                        logger.info(
                            f"gpg import key result return code {result.results[0]["ok"]}. reason: {result.ok_reason[result.results[0]["ok"]]}"
                        )

        self.keyring_ok = True
        logger.info("keyring check completed successfully")

    def fingerprint_in_keyring(self) -> bool:
        keyring = self.gpg.list_keys()
        if self.recipients in keyring.fingerprints:
            return True
        return False

    def encrypt_file(self, input: str, output: str) -> None:
        if not self.keyring_ok:
            self.check_keyring()
        with open(input, "rb") as f:
            status = self.gpg.encrypt_file(
                f,
                recipients=self.recipients,
                output=output,
                always_trust=True,
                armor=False,
                extra_args=["-z", "-1", "--cipher-algo", "AES256"],
            )
        if status.ok:
            logger.info(f"encryption successful. reason: {status.status}")
        else:
            logger.error(
                f"encryption failed. reason: {status.status} - {status.status_detail}"
            )
