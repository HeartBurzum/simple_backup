from setuptools import find_packages, setup

setup(
    name="simple_backup",
    version="0.1",
    entry_points={"console_scripts": ["simple_backup-run = simplebackup.app:main"]},
    packages=[
        "simplebackup",
        "simplebackup.backup",
        "simplebackup.config",
        "simplebackup.encryption",
    ],
)
