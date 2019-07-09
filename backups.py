#!/usr/bin/env python
"""Docker Compose Postgres dump and backup script

This script can be used to easily create dumps of postgres databases in docker containers,
upload them to rclone targets and restore them if needed.

It can also simply create archives of any folder (for example a postgres volume mapping) and restore/sync them.

Requires the docker container to be setup with docker compose.
"""
import os
import glob
import argparse
import datetime
import shutil
import configparser
import tarfile
import time

storage_dir = ''
dump_filename = ''
backup_filename = ''
backup_timestamp = True
backup_timestamp_format = ''
backup_source = ''
docker_compose_path = ''
pg_docker_container = ''
pg_docker_user = ''
rclone_target = ''
rclone_path = ''
delete_days = 7

BACKUP_EXTENSION = '.tar.gz'
DUMP_EXTENSION = '.sql'

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('config', help="config from config.ini that should be used", nargs='?', default='default')

    parser.add_argument("-d", '--dump', help="dump postgres database", action="store_true")
    parser.add_argument("-b", '--backup', help="create postgres folder backup", action="store_true")

    parser.add_argument("-l", '--load', help="load latest dump", action="store_true")  # TODO implement
    parser.add_argument("-L", '--load-specific', help="load specified dump")

    parser.add_argument("-r", '--restore', help="restore latest backup", action="store_true")  # TODO implement
    parser.add_argument("-R", '--restore-specific', help="restore specified backup")

    parser.add_argument("-o", '--delete', help="delete backups older than a certain amount of days")  # TODO implement

    return parser.parse_args()


def make_backup_dir():
    if not os.path.exists(storage_dir):
        print('Created Backup directory!')
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

    print("Creating backup ...")
    tar = tarfile.open(get_backup_path(), "w:gz")
    tar.add(backup_source, filter=reset)
    tar.close()
    print("Backup created!")


def restore_backup(filename):
    print("Restoring backup ...")
    os.chdir(docker_compose_path)
    os.system('docker-compose stop ' + pg_docker_container)

    shutil.rmtree(backup_source, ignore_errors=False, onerror=None)

    os.makedirs(backup_source)

    tar = tarfile.open(filename)
    tar.extractall(path=(os.path.abspath(os.path.join(backup_source, '..'))))
    tar.close()

    os.system('docker-compose up -d ' + pg_docker_container)
    print("Backup restored!")


def get_dump_path():
    return file_timestamp(storage_dir + dump_filename) + '.sql'


def create_pg_dump():
    print("Creating DB dump ... ")
    os.chdir(docker_compose_path)
    out = os.popen('docker-compose up -d ' + pg_docker_container).read()
    os.system('docker-compose exec ' + pg_docker_container + ' pg_dumpall -U ' + pg_docker_user + ' > ' + get_dump_path())
    if 'is up-to-date' in out:
        os.system('docker-compose stop ' + pg_docker_container)
    print("DB dump created in " + get_dump_path())


def load_pg_dump(file):
    print("Loading DB dump ... ")
    os.chdir(docker_compose_path)
    os.system('docker-compose stop ' + pg_docker_container)

    shutil.rmtree(backup_source, ignore_errors=False, onerror=None)

    os.system('docker-compose up -d ' + pg_docker_container)

    time.sleep(2)
    os.system('docker-compose exec -T ' + pg_docker_container + ' psql -U ' + pg_docker_user + ' postgres < ' + file)

    print("DB dump loaded!")


def choose_file(extension):
    dir_list = os.listdir(storage_dir)
    print(storage_dir)
    if len(dir_list) == 0:
        print('There where no ' + extension + ' files found that could be restored!')
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


def get_latest(extension):
    print('Searching latest ' + extension)
    list_of_files = glob.glob(storage_dir + '*' + extension)

    if len(list_of_files) == 0:
        print('There where no ' + extension + ' files found that could be restored!')
        return

    filename = max(list_of_files, key=os.path.getctime)

    print("Found " + filename)

    if extension == DUMP_EXTENSION:
        load_pg_dump(filename)

    if extension == BACKUP_EXTENSION:
        restore_backup(filename)


def sync_storage():
    if rclone_target == '':
        return

    print('Starting backup sync ...')
    os.system('rclone sync ' + storage_dir + ' ' + rclone_target + ':' + rclone_path)
    print('Storage directory synced!')


def delete_old():
    if delete_days == -1:
        return

    print("Deleting old backups ...")

    cutoff = time.time() - (delete_days * 86400)

    files = os.listdir(storage_dir)

    for f in files:
        if os.path.isfile(storage_dir + f):
            t = os.stat(storage_dir + f)
            c = t.st_ctime

            if c < cutoff:
                os.remove(storage_dir + f)

    print('Finished deleting old backups.')


def load_config(config_name):
    global storage_dir, dump_filename, backup_filename, backup_timestamp, backup_timestamp_format, backup_source, pg_docker_container, pg_docker_user, rclone_target, rclone_path, delete_days,docker_compose_path

    config = configparser.ConfigParser()
    config.read("config.ini")

    storage_dir = config.get(config_name, "storage_dir")
    dump_filename = config.get(config_name, "dump_filename")
    backup_filename = config.get(config_name, "backup_filename")
    backup_timestamp = config.get(config_name, "backup_timestamp")
    backup_timestamp_format = config.get(config_name, "backup_timestamp_format")
    backup_source = config.get(config_name, "backup_source")
    docker_compose_path = config.get(config_name, "docker_compose_path")
    pg_docker_container = config.get(config_name, "pg_docker_container")
    pg_docker_user = config.get(config_name, "pg_docker_user")
    rclone_target = config.get(config_name, "rclone_target")
    rclone_path = config.get(config_name, "rclone_path")
    delete_days = int(config.get(config_name, "delete_days"))

    if not storage_dir.endswith("/"):
        storage_dir += "/"

    if not docker_compose_path.endswith("/"):
        docker_compose_path += "/"

    if not backup_source.endswith("/"):
        backup_source += "/"


def main():
    args = parse_args()

    load_config(args.config)

    make_backup_dir()

    if args.backup:
        create_backup()

    if args.dump:
        create_pg_dump()

    if args.load_specific:
        choose_file(DUMP_EXTENSION)

    if args.restore_specific:
        choose_file(BACKUP_EXTENSION)

    if args.load:
        get_latest(DUMP_EXTENSION)

    if args.restore:
        get_latest(BACKUP_EXTENSION)

    if args.backup or args.dump:
        delete_old()
        sync_storage()


if __name__ == "__main__":
    main()
