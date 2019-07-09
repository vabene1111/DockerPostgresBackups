# Docker Postgres Backup
This script is primarily intended to make it easier to backup and restore postgres database containers running with 
docker compose but it can also be used to backup any other directory.

**Features**
- Dump data from postgresql containers
- Load dumps back into postgresql containers
- Create folder backups
- Restore folder backups
- Sync backups to basically any cloud provider using rclone

## Installation / Usage
1. Clone this repository to your desired location.
2. Install requirements using `pip install -r requirements.txt`
3. Create config using `cp config.ini.template config.ini`
    - Adjust config to your needs
4. Run `python backups.py` with your desired command line arguments

```
usage: backups.py [-h] [-d] [-b] [-l] [-L LOAD_SPECIFIC] [-r]
                  [-R RESTORE_SPECIFIC] [-o DELETE]
                  [config]

positional arguments:
  config                config from config.ini that should be used

optional arguments:
  -h, --help            show this help message and exit
  -d, --dump            dump postgres database
  -b, --backup          create postgres folder backup
  -l, --load            load latest dump
  -L LOAD_SPECIFIC, --load-specific LOAD_SPECIFIC
                        load specified dump
  -r, --restore         restore latest backup
  -R RESTORE_SPECIFIC, --restore-specific RESTORE_SPECIFIC
                        restore specified backup
  -o DELETE, --delete DELETE
                        delete backups older than a certain amount of days
```

## License
See [LICENS.md](https://github.com/vabene1111/DockerPostgresBackups/blob/master/LICENSE.md)