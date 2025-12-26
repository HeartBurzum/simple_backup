import logging

from simplebackup.backup.backup import Backup
from simplebackup.config.config import Config

logger = logging.getLogger(__name__)


def main():
    config = Config()

    backup = Backup(config)


if __name__ == "__main__":
    main()
