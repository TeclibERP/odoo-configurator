# -*- coding: utf-8 -*-
# Copyright (C) 2023 - Teclib'ERP (<https://www.teclib-erp.com>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import os
from .logging import get_logger
from pykeepass import PyKeePass
import cryptocode

logger = get_logger(__name__)
CACHE = "/tmp/.configurator_cache"


class PasswordManager:

    def __init__(self, password):
        self._keepass_password = password

    def get_keepass(self, filename):
        return PyKeePass(os.getenv("HOME") + "/" + filename, password=self._keepass_password)

    def get_keepass_entry(self, filename, group, entry):
        kp = self.get_keepass(filename)
        kgroup = kp.find_groups(name=group, first=True)
        if kgroup:
            kentry = kp.find_entries(title=entry, group=kgroup, recursive=False, first=True)
            if kentry:
                return kentry
            else:
                logger.error("Cannot find %s in %s" % (entry, group))
                raise Exception("Cannot find %s in %s" % (entry, group))
        else:
            logger.error("Cannot find %s" % group)
            raise Exception("Cannot find %s" % group)
        return False

    def get_keepass_entry_value(self, filename, group, entry, field, default='admin'):
        try:
            entry = self.get_keepass_entry(filename, group, entry)
        except Exception as err:
            logger.error(type(err).__name__)
            return False
        if entry:
            return eval('entry.' + field)
        return default

    def get_keepass_password(self, filename, group, entry):
        return self.get_keepass_entry_value(filename, group, entry, 'password')

    def get_keepass_password_crypt(self, filename, group, entry, key):
        return cryptocode.encrypt(self.get_keepass_entry_value(filename, group, entry, 'password'), key)

    def get_keepass_user(self, filename, group, entry):
        return self.get_keepass_entry_value(filename, group, entry, 'username')

    def get_keepass_url(self, filename, group, entry):
        kp_url = self.get_keepass_entry_value(filename, group, entry, 'url')
        if kp_url and kp_url[-1] == '/':
            kp_url = kp_url[:-1]
        return kp_url
