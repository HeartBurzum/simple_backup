from backup import Backup
from config import Config
from encryption import Encrypt

if __name__ == "__main__":
    config = Config()
    backup = Backup(config)
    if config.encryption_enabled:
        encrypt = Encrypt(config, backup.tar_files)
