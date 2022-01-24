# Warning
This script is just an old relict of me not having found any appropriate tool to backup postgres databases inside docker containers. 
In the meantime several other peopel have build better systems so **I do NOT recommend using this script**, its just here for legacy purposes and if anyone finds the code useful.
You may want to try this tool https://github.com/prodrigestivill/docker-postgres-backup-local

# Docker Postgres Backup
This script is primarily intended to make it easier to backup and restore postgres database containers running with 
docker compose but it can also be used to backup any other directory.

## Features

**Dump** postgres databases into files with customizable prefixes and timestamps.  
Quickly **load** dumps back into the database trough an interactive command or simply load the latest backup.  
**Sync** backups via rclone to basically any storage provider.

## Installation / Usage
1. Clone this repository to your desired location.
2. Install requirements using `pip install -r requirements.txt`
3. Create config using `cp config.ini.template config.ini`
    - Adjust config to your needs
4. Run `python backups.py` with your desired command line arguments

```
usage: backups.py [-h] [-d] [-l] [-L LOAD_SPECIFIC] [-s] [-v] [config]

positional arguments:
  config                config from config.ini that should be used

optional arguments:
  -h, --help            show this help message and exit
  -d, --dump            dump postgres database
  -l, --load            load latest dump
  -L LOAD_SPECIFIC, --load-specific LOAD_SPECIFIC
                        load specified dump
  -s, --sync            sync backups with rclone target
  -v, --verbose         enables debugging output
```

### Cron Example
```sh
0 5 * * * cd /usr/src/backup && /usr/bin/python /usr/src/backups/backups.py -d homepage
```

### rclone
If you want to use the rclone features you will need to install rclone.
Visit their website for more info https://rclone.org/

## License
See [LICENS.md](https://github.com/vabene1111/DockerPostgresBackups/blob/master/LICENSE.md)
