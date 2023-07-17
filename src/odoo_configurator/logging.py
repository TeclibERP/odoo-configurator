# -*- coding: utf-8 -*-
# Copyright (C) 2023 - Teclib'ERP (<https://www.teclib-erp.com>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import logging


def get_logger(name):
    logger = logging.getLogger(name)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s : %(message)s')
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.handlers.clear()
    logger.addHandler(ch)
    logger.setLevel(logging.INFO)
    return logger
