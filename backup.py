import logging
import os
import tarfile

from config import Config

log_level = logging.INFO
log_format = "[%(asctime)s][%(levelname)s][%(module)s] %(message)s"
logging.basicConfig(level=log_level, format=log_format)
logger = logging.getLogger(name=__name__)


class Backup:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.tar_files = []
        self.backup()

    def backup(self):
        errors = 0
        for path in self.config.backup_path_list:
            logger.debug(f"Current path: {path}")
            try:
                tar_file_name = path.split("/")[-1]
                tar_file_full_path = f"{self.config.data_dir}/{self.config.timestamp}-{tar_file_name}.tar.gz"
                with tarfile.open(name=f"{tar_file_full_path}", mode="w:gz") as tar:
                    try:
                        tar.add(f"{path}")
                    except FileNotFoundError as e:
                        logger.error(f"Unable to add {path} to tarball. Reason: {e}")
                        os.remove(tar_file_full_path)
                        errors += 1
                        continue
            except PermissionError as e:
                errors += 1
                logger.error(f"Access was denied while creating tarball. {e}")
                continue
            logger.info(
                f"Successfully created tarfile for {path=}. {tar_file_full_path}"
            )
            self.tar_files.append(tar_file_full_path)

        if self.config.encryption_enabled:
            logger.info(f"Tarball creation completed with {errors} errors.")
        else:
            logger.info(f"Backup completed with {errors} errors.")
