#!/usr/bin/env python
"""Docker Compose Postgres dump and backup script

This script can be used to easily create dumps of postgres databases in docker containers,
upload them to rclone targets and restore them if needed.

It can also simply create archives of any folder (for example a postgres volume mapping) and restore/sync them.

Requires the docker container to be setup with docker compose.
"""
import os
import argparse
import datetime
import shutil
import sys
import tarfile
import time

# --------------- CONFIG ---------------

# Local directory to store backups in
storage_dir = './backups/'

# Filename of the data directory backup archive
dump_filename = 'dump_'

# Filename of the postgres dump file
backup_filename = 'backup_'

# Include a timestamp in backup/dump filenames
backup_timestamp = True

# Define the format for timestamps (see http://strftime.org/ for format info)
backup_timestamp_format = '%Y-%m-%d_%H-%M-%S'

# Postgres data directory (mapping of data dir in postgres container)
backup_source = 'test_folder'

# Name of the postgres docker container
pg_docker_container = 'db'

# Username to use when dumping data
pg_docker_user = 'dbuser'

# Name of the rclone target
rclone_target = ''  # TODO implement

# Path on the rclone target
rclone_path = ''

# --------------- CONFIG ---------------

BACKUP_EXTENSION = '.tar.gz'
DUMP_EXTENSION = '.sql'

if not storage_dir.endswith("/"):
    storage_dir += "/"


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('config', nargs='?', default='default_config.py')  # TODO implement

    parser.add_argument("-d", '--dump', help="dump postgres database", action="store_true")
    parser.add_argument("-b", '--backup', help="create postgres folder backup", action="store_true")

    parser.add_argument("-l", '--load', help="load latest dump", action="store_true")  # TODO implement
    parser.add_argument("-L", '--load-specific', help="load specified dump")  # TODO implement

    parser.add_argument("-r", '--restore', help="restore latest backup", action="store_true")  # TODO implement
    parser.add_argument("-R", '--restore-specific', help="restore specified backup")  # TODO implement

    parser.add_argument("-o", '--delete', help="delete backups older than a certain amount of days")  # TODO implement

    return parser.parse_args()


def make_backup_dir():
    if not os.path.exists(storage_dir):
        os.makedirs(storage_dir)


def file_timestamp(file):
    if backup_timestamp:
        now = datetime.datetime.now()
        timestamp = now.strftime(backup_timestamp_format)

        file = file + timestamp
    return file


def get_backup_path():
    return file_timestamp(storage_dir + backup_filename) + '.tar.gz'


def create_backup():
    def reset(tarinfo):
        tarinfo.uid = tarinfo.gid = 0
        tarinfo.uname = tarinfo.gname = "root"  # TODO verify permissions work
        return tarinfo

    tar = tarfile.open(get_backup_path(), "w:gz")
    tar.add(backup_source, filter=reset)
    tar.close()


def restore_backup(filename):
    shutil.rmtree(backup_source, ignore_errors=False, onerror=None)

    tar = tarfile.open(filename)
    tar.extractall(path=(os.path.abspath(os.path.join(backup_source, '..'))))
    tar.close()


def get_dump_path():
    return file_timestamp(storage_dir + dump_filename) + '.sql'


def create_pg_dump():
    os.system('docker-compose exec ' + pg_docker_container + ' pg_dumpall -U ' + pg_docker_user + ' > ' + get_dump_path())


def load_pg_dump(file):
    os.system('docker-compose up -d' + pg_docker_container)
    time.sleep(2)
    os.system('docker-compose exec -T ' + pg_docker_container + ' psql -U ' + pg_docker_user + ' postgres < ' + file)
    os.system('docker-compose stop ' + pg_docker_container)


def choose_file(extension):
    dir_list = os.listdir(storage_dir)

    if len(dir_list) == 0:
        print('There where no files found that could be restored!')
        return

    print("Please choose the file you want to restore:")
    file_chooser = ""
    i = 0
    for file in dir_list:
        if file.endswith(extension):
            file_chooser += '[' + str(i) + '] ' + file + '  '
            i += 1
            if i % 3 == 0:
                file_chooser += '\n'

    print(file_chooser)

    file_index = int(input())
    filename = storage_dir + dir_list[file_index]

    if extension == DUMP_EXTENSION:
        load_pg_dump(filename)

    if extension == BACKUP_EXTENSION:
        restore_backup(filename)


def sync_storage():
    if rclone_target == '':
        return

    os.system('rclone sync ' + storage_dir + ' ' + rclone_target + ':' + rclone_path)


def main():
    args = parse_args()

    make_backup_dir()

    if args.backup:
        create_backup()

    if args.dump:
        create_pg_dump()

    if args.load:
        choose_file(DUMP_EXTENSION)

    if args.restore:
        choose_file(BACKUP_EXTENSION)

    sync_storage()


if __name__ == "__main__":
    main()
