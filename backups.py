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
filename_prefix = ''
timestamp = True
timestamp_format = ''
docker_compose_path = ''
pg_data_dir = ''
pg_docker_container = ''
pg_docker_user = ''
rclone_target = ''
rclone_path = ''
delete_days = 7

DUMP_EXTENSION = '.sql'

DEBUG = False


def debug(msg):
    if DEBUG:
        print(msg)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('config', help="config from config.ini that should be used", nargs='?', default='default')

    parser.add_argument("-d", '--dump', help="dump postgres database", action="store_true")
    
    parser.add_argument("-l", '--load', help="load latest dump", action="store_true")
    parser.add_argument("-L", '--load-specific', help="load specified dump")

    parser.add_argument("-s", '--sync', help="pushes/syncs backups with rclone target", action="store_true")
    parser.add_argument("-p", '--pull', help="pulls backups from rclone target", action="store_true")

    parser.add_argument("-v", '--verbose', help="enables debugging output", action="store_true")

    return parser.parse_args()


def make_storage_dir():
    if not os.path.exists(storage_dir):
        print('Created storage directory!')
        os.makedirs(storage_dir)


def file_timestamp(file):
    if timestamp:
        now = datetime.datetime.now()
        ts = now.strftime(timestamp_format)

        file = file + ts
    return file


def get_dump_path():
    return file_timestamp(storage_dir + filename_prefix) + DUMP_EXTENSION


def create_pg_dump():
    print("Creating DB dump ... ")
    os.chdir(docker_compose_path)
    cmd_container_up = '/usr/bin/docker compose up -d ' + pg_docker_container

    debug('starting container: ' + cmd_container_up)

    out = os.popen(cmd_container_up).read()

    cmd_container_dump = '/usr/bin/docker compose exec -T ' + pg_docker_container + ' pg_dumpall -U ' + pg_docker_user + ' -f /var/lib/postgresql/data/dump' + DUMP_EXTENSION

    debug('creating dump: ' + cmd_container_dump)

    os.system(cmd_container_dump)

    mv = 'mv ' + pg_data_dir + 'dump' + DUMP_EXTENSION + ' ' + get_dump_path()
    os.system(mv)

    debug('moving backup with: ' + mv)

    if 'is up-to-date' in out:
        os.system('/usr/bin/docker compose stop ' + pg_docker_container)
    print("DB dump created in " + get_dump_path())


def load_pg_dump(file):
    print("Loading DB dump ... ")
    os.chdir(docker_compose_path)
    os.system('/usr/bin/docker compose stop ' + pg_docker_container)

    if os.path.exists(pg_data_dir):
        shutil.rmtree(pg_data_dir, ignore_errors=False, onerror=None)

    os.system('/usr/bin/docker compose up -d ' + pg_docker_container)

    time.sleep(2)
    os.system('/usr/bin/docker compose exec -T ' + pg_docker_container + ' psql -U ' + pg_docker_user + ' postgres < ' + file)

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

    load_pg_dump(filename)


def get_latest():
    print('Searching latest ' + DUMP_EXTENSION)
    list_of_files = glob.glob(storage_dir + '*' + DUMP_EXTENSION)

    if len(list_of_files) == 0:
        print('There where no ' + DUMP_EXTENSION + ' files found that could be restored!')
        return

    filename = max(list_of_files, key=os.path.getctime)

    print("Found " + filename)

    load_pg_dump(filename)


def sync_storage():
    if rclone_target == '':
        return

    print('Starting backup sync ...')

    cmd = 'rclone sync ' + storage_dir + ' ' + rclone_target + ':' + rclone_path
    if DEBUG:
        print('rclone command: ' + cmd)

    os.system(cmd)

    print('Storage directory synced!')


def pull_storage():
    if rclone_target == '':
        return

    print('Starting retrieving backups from sync target ...')

    cmd = 'rclone sync '  + rclone_target + ':' + rclone_path + ' ' + storage_dir
    if DEBUG:
        print('rclone command: ' + cmd)

    os.system(cmd)

    print('Storage directory pulled!')


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
    # config parser infos https://docs.python.org/3/library/configparser.html
    # config.sections() all sections for all parameter
    global storage_dir, filename_prefix, timestamp, timestamp_format, pg_data_dir, pg_docker_container, pg_docker_user, rclone_target, rclone_path, delete_days, docker_compose_path

    config = configparser.ConfigParser()
    config.read("config.ini")

    storage_dir = config.get(config_name, "storage_dir")
    filename_prefix = config.get(config_name, "filename_prefix")
    timestamp = config.get(config_name, "timestamp")
    timestamp_format = config.get(config_name, "timestamp_format")
    docker_compose_path = config.get(config_name, "docker_compose_path")
    pg_data_dir = config.get(config_name, "pg_data_dir")
    pg_docker_container = config.get(config_name, "pg_docker_container")
    pg_docker_user = config.get(config_name, "pg_docker_user")
    rclone_target = config.get(config_name, "rclone_target")
    rclone_path = config.get(config_name, "rclone_path")
    delete_days = int(config.get(config_name, "delete_days"))

    if not storage_dir.endswith("/"):
        storage_dir += "/"

    if not docker_compose_path.endswith("/"):
        docker_compose_path += "/"

    if not pg_data_dir.endswith("/"):
        pg_data_dir += "/"


def main():
    global DEBUG
    args = parse_args()

    if args.verbose:
        DEBUG = True

    if DEBUG:
        print('Loading Config:' + args.config)
    load_config(args.config)

    make_storage_dir()

    if args.dump:
        create_pg_dump()

    if args.load_specific:
        choose_file(DUMP_EXTENSION)

    if args.load:
        get_latest()

    if args.dump:
        delete_old()

    if args.dump or args.sync:
        sync_storage()

    if args.pull:
        pull_storage()


if __name__ == "__main__":
    main()
