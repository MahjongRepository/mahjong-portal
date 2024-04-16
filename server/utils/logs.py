# -*- coding: utf-8 -*-

import datetime
import logging
import os

from django.conf import settings

logger = logging.getLogger()


def set_up_logging(prefix: str):
    logs_directory = os.path.join(settings.BASE_DIR, "..", "logs")
    if not os.path.exists(logs_directory):
        os.mkdir(logs_directory)

    logger.setLevel(logging.NOTSET)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    file_name = "{}_{}.log".format(prefix, datetime.datetime.now().strftime("%Y-%m-%d_%H_%M_%S"))
    fh = logging.FileHandler(os.path.join(logs_directory, file_name))
    fh.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)
