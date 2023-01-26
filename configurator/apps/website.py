# -*- coding: utf-8 -*-
# Copyright (C) 2023 - Teclib'ERP (<https://www.teclib-erp.com>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from . import base
from .modules import OdooModules


class OdooWebsite(base.OdooModule):
    _name = "Website"
    _key = "website"

    def apply(self):
        super(OdooWebsite, self).apply()

        theme = self._datas.get(self._key, {}).get("theme", False)
        if theme:
            OdooModules(self._configurator).install_odoo_theme(theme)
