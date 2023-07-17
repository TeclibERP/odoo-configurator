from . import base
from .modules import OdooModules
import requests
import json
import os

# -*- coding: utf-8 -*-
# Copyright (C) 2023 - Teclib'ERP (<https://www.teclib-erp.com>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

class Mattermost(base.OdooModule):
    _name = "Mattermost"
    _key = "mattermost"

    def apply(self):
        super(Mattermost, self).apply()
        if self._datas.get('no_notification', False):
            return

        mattermost_channel = self._datas.get('mattermost_channel', False)
        mattermost_url = self._datas.get('mattermost_url', False)

        if not mattermost_channel or not mattermost_url:
            return

        headers = {}
        values = {
            "username": "Configurator : %s" % (os.getlogin()),
            "channel": mattermost_channel,
            "text": """#### Odoo %s updated with Configurator
- Url : %s
- Db : %s
- User : %s""" % (self._datas.get('name', "NONAME"),
                  self._datas.get('auth', {}).get('odoo', {}).get('url'),
                  self._datas.get('auth', {}).get('odoo', {}).get('dbname'),
                  self._datas.get('auth', {}).get('odoo', {}).get('username'),
                  )
        }
        if "localhost" not in self._datas.get('auth', {}).get('odoo', {}).get('url'):
            response = requests.post(mattermost_url,
                                     headers=headers, data=json.dumps(values))
        else:
            print("No send notification on localhost")
