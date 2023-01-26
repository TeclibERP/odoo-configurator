# -*- coding: utf-8 -*-
# Copyright (C) 2023 - Teclib'ERP (<https://www.teclib-erp.com>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from . import base


class OdooConnection(base.OdooModule):
    _name = "Auth"
    _key = "auth"

    def apply(self):
        pass
