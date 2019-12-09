[![Build Status](https://travis-ci.org/MahjongRepository/mahjong-portal.svg?branch=master)](https://travis-ci.org/MahjongRepository/mahjong-portal)

It is working with Python **3.6+** only.

The project is web-application to accumulate, calculate and display russian riichi-mahjong tournaments and ratings.

# Docker Local Development

## Set up

You need to have installed docker and docker compose.

Steps to run the project:

1. `make build`
2. `make initial_data` (run this command only once, for the initial project setup)
3. `make up`

After these steps you will be able to access website here: http://0.0.0.0:8060/
