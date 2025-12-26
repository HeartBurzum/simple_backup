import logging
import os
import sys
from typing import Union

import gnupg

logger = logging.getLogger(__name__)


class Encrypt:
    def __init__(
        self,
        fingerprints: Union[str, list[str]],
        data_dir: str,
        key_directory: str,
        remove_unencrypted: bool,
    ):
        self.gpg = gnupg.GPG(gnupghome=f"{data_dir}/keyring")
        self.recipients = fingerprints
        self.public_key_dir = key_directory
        self.remove_unencrypted = remove_unencrypted
        self.keyring_ok = False

        try:
            self.public_key_dir_filelist = os.listdir(self.public_key_dir)
        except FileNotFoundError as e:
            logger.error(
                f"Unable to find public keys, check SIMPLE_BACKUP_ENCRYPTION_PUBLIC_KEY_DIR value. Aborting...\n{e}"
            )
            sys.exit(1)

    def start_encryption(self, files: Union[str, list[str]]):
        logger.debug(f"start_encryption {files=}")
        if type(files) == str:
            self.encrypt_file(str(files), f"{files}.asc")
        else:
            for file in files:
                self.encrypt_file(file, f"{file}.asc")

    def check_keyring(self):
        missing = self.fingerprint_in_keyring()
        if not missing:
            logger.info("All fingerprints have imported keys")
            return
        else:
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
                    with open(f"{self.public_key_dir}/{file}", "r") as key_file:
                        text = key_file.read()
                    keys = self.gpg.scan_keys_mem(text)
                    logger.debug(f"key read {keys.fingerprints}")
                    for fingerprint in keys.fingerprints:
                        if fingerprint in missing:
                            result = self.gpg.import_keys(text)
                            missing.remove(fingerprint)
                            logger.info(
                                f"gpg import key result return code {result.results[0]["ok"]}. reason: {result.ok_reason[result.results[0]["ok"]]}"
                            )

        if missing:
            logger.critical(
                f"Missing public key(s) for {missing}. Add public keys or remove the fingerprint. Exiting with errors..."
            )
            sys.exit(1)
        else:
            self.keyring_ok = True
            logger.info("All supplied fingerprint keys added to keyring.")

    def fingerprint_in_keyring(self) -> list[str]:
        keyring = self.gpg.list_keys()
        logger.debug(f"{self.recipients=} {keyring.fingerprints=}")
        missing = list(set(self.recipients) - set(keyring.fingerprints))
        if not missing:
            logger.debug("all recipients on keyring")
        else:
            logger.info(f"Not all recipients on keyring, missing keys: {missing}")
        return missing

    def encrypt_file(self, input: str, output: str) -> None:
        logger.debug(f"encrypt_file {input=} {output=}")
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
            if self.remove_unencrypted:
                logger.debug(f"removing unencryped file {input}")
                os.remove(input)
        else:
            logger.error(
                f"encryption failed. reason: {status.status} - {status.status_detail}"
            )
