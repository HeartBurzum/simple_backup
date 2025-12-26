import logging
import os
import tarfile
from datetime import datetime
from typing import Union

from simplebackup.config.config import Config

logger = logging.getLogger(name=__name__)


class Backup:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.backup()

    def backup(self):
        errors = 0
        for path in self.config.backup_path_list:
            logger.debug(f"Current path: {path}")
            try:
                directory_name = path.split("/")[-1]
                tar_file_full_path = f"{self.config.data_dir}/{self.config.timestamp}-{directory_name}.tar.gz"
                with tarfile.open(name=f"{tar_file_full_path}", mode="w:gz") as tar:
                    try:
                        tar.add(f"{path}")
                    except FileNotFoundError as e:
                        logger.error(f"Unable to add {path} to tarball. Reason: {e}")
                        os.remove(tar_file_full_path)
                        errors += 1
                        continue

                if self.config.encryption_enabled:
                    self.config.encryptor.start_encryption(tar_file_full_path)
            except PermissionError as e:
                errors += 1
                logger.error(f"Access was denied while creating tarball. {e}")
                continue

            logger.info(
                f"Successfully created tarfile for {path=}. {tar_file_full_path}"
            )

            # Check for how many backups of the directory we have.
            if self.config.num_copies > 0:
                self.existing_backups(directory_name)

        logger.info(f"Backup completed with {errors} errors.")

    def existing_backups(self, directory_name: str) -> None:
        """
        we stat on each creation - extra calls, safer
        """
        logger.debug(f"existing_backups: {directory_name=}")
        data_files = os.listdir(self.config.data_dir)
        existing_files = list()
        for file in data_files:
            l: list[Union[float, str]] = file.split("-")  # pyright: ignore
            if l[2] in (f"{directory_name}.tar.gz", f"{directory_name}.tar.gz.asc"):
                l.append(file)
                # list(timestamp cal, timestamp time, file_name, full_name)
                # list makes this hard to read - redo in the future
                dt: str = l.pop(0) + l.pop(0)  # pyright: ignore
                try:
                    timestamp = datetime.strptime(dt, "%Y%m%d%H%M%S").timestamp()
                except ValueError:
                    logger.warning(
                        f"Found file in backup directory that does not have a parsable timestamp. {file}"
                    )
                    continue
                l.insert(0, timestamp)
                # list(timestamp, file_name, full_name)
                logger.debug(f"Found {l[2]} in backup directory.")
                existing_files.append(l)

        existing_files.sort(key=lambda f: f[0])
        logger.info(f"{len(existing_files)} existing backups for {directory_name}.")
        logger.debug(f"{existing_files}")
        while len(existing_files) > self.config.num_copies:
            delete = existing_files.pop(0)
            path = f"{self.config.data_dir}/{delete[2]}"
            if os.access(path, os.W_OK):
                logger.info(f"Deleting copy {path}.")
                os.remove(path)
