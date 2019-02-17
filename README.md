[![Build Status](https://travis-ci.org/MahjongRepository/mahjong-portal.svg?branch=master)](https://travis-ci.org/MahjongRepository/mahjong-portal)

It is working with Python **3.6+** only.

Web-application to accumulate, calculate and display russian riichi-mahjong tournaments and ratings.

# Local development

## Set up

You need to have installed docker and docker compose.

Steps to run the project:

1. `make build`
2. `make up`

After that you will be able to access website here: http://0.0.0.0:8010/

# DB restore

1. put database .sql backup to `initdb.d` folder
2. `make restore_db`

