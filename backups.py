#!/usr/bin/env python
"""Docker Compose Postgres Backup Script

This script can be used to easily create backups of postgres databases in docker containers,
upload them to rclone targets and restore them if needed.

Requires the docker container to be run through docker compose.
"""
import os
import argparse
import datetime
import tarfile

# --------------- CONFIG ---------------

# Local directory to store backups in
backups_dir = './backups/'

# Filename of the data directory backup archive
backup_filename_full = 'dump_'

# Filename of the postgres dump file
backup_filename_dump = 'backup_'

# Include a timestamp in backup filenames
backup_timestamp = True

# Define the format for timestamps (see http://strftime.org/ for format info)
backup_timestamp_format = '%Y-%m-%d_%H-%M-%S'

# Name of the postgres docker container
docker_container = 'db'

# Postgres data directory (mapping of data dir in postgres container)
postgres_data_dir = 'venv'

# Name of the rclone target
rclone_target = ''

# Path on the rclone target
rclone_path = ''

# --------------- CONFIG ---------------

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", help="path to mod root directory (not addons)")
    parser.add_argument("-k", "--public-key-path",
                        help="path to directory for storing generated public key (default <base path>/keys)")

    return parser.parse_args()


def make_backup_dir():
    if not os.path.exists(backups_dir):
        os.makedirs(backups_dir)


def create_config():
    f = open('test', "w")
    f.write("")
    f.close()


def backup_data_dir():
    def reset(tarinfo):
        tarinfo.uid = tarinfo.gid = 0
        tarinfo.uname = tarinfo.gname = "root"  # TODO verify permissions work
        return tarinfo

    backup_file = backups_dir + backup_filename_dump

    if backup_timestamp:
        now = datetime.datetime.now()
        timestamp = now.strftime(backup_timestamp_format)

        backup_file = backup_file + timestamp

    tar = tarfile.open(backup_file + '.tar.gz', "w:gz")
    tar.add(postgres_data_dir, filter=reset)
    tar.close()


def main():
    args = parse_args()

    make_backup_dir()

    backup_data_dir()


if __name__ == "__main__":
    main()
