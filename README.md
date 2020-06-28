It is working with Python **3.6+** only.

The project is web-application to accumulate, calculate and display russian riichi-mahjong tournaments and ratings.

# Local

## Project set up

You need to have installed docker and docker compose.

Steps to run the project:

1. `make build_docker`
2. `make initial_data` (run this command only once, for the initial project setup)
3. `make up`

After these steps you will be able to access website here: http://0.0.0.0:8060/

## Development workflow

1. Install to your host system `sudo pip3 install pre-commit==2.1.0`
2. `pre-commit install`

# Production

## Docker set up

You need to have installed docker and docker compose.

Copy `.envs/.production.env.example` file and fill it with real data, but don't forget to keep it in secret (at least don't add it to version control system). Assign these env variables to the container with any way that is suits you (there are different options how to do it), and after that you can simply run `make build` and `make up` commands. By default in `production.yml` we are using `.envs/.production.env` file.

For static files serving and SSL configuration you need to set up the server upfront of this docker image.

If needed, restore the database backup for the new installation.

## DB Backups

On your host machine you can set up these cron commands to make backups:

```
# every 6 hours
0 */6 * * * /usr/local/bin/docker-compose -f /path/to/project/production.yml run --rm db bash backup.sh hourly
# once a week
0 0 * * 0 /usr/local/bin/docker-compose -f /path/to/project/production.yml run --rm db bash backup.sh weekly
# once a month
0 0 1 * * /usr/local/bin/docker-compose -f /path/to/project/production.yml run --rm db bash backup.sh monthly
```
