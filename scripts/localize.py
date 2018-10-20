#!/usr/bin/env python3
"""Script to convert example config to host-specific.

Usage:
    python localize.py < settings/local.example.py > settings/local.py

"""
from os import environ

DEFAULTS = {
    'SECRET_KEY': '--SECRET_KEY--',
    'HOST': '*',
    'DB_HOST': 'postgres',
    'DB_PORT': '5432',
    'DB_NAME': 'mahjong_portal',
    'DB_USER': 'mahjong_portal',
    'DB_PASSWORD': '--DB_PASSWORD--',
}


def main():
    while True:
        try:
            line = input()
        except (EOFError, KeyboardInterrupt):
            break
        line_split = line.split('--')
        if not (len(line_split) & 1):
            raise SyntaxError(f'Wrong double-dash count in line {line!r}')
        for i in range(1, len(line_split), 2):
            line_split[i] = environ.get(line_split[i], DEFAULTS[line_split[i]])
        line = ''.join(line_split)
        print(line)


if __name__ == '__main__':
    main()
