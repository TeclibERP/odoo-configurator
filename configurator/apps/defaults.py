# -*- coding: utf-8 -*-
# Copyright (C) 2023 - Teclib'ERP (<https://www.teclib-erp.com>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from collections import OrderedDict

from . import base


class OdooDefaults(base.OdooModule):
    _name = "Defaults"

    def apply(self):
        super(OdooDefaults, self).apply()

        for key in self._datas:
            if isinstance(self._datas.get(key), dict) or isinstance(self._datas.get(key), OrderedDict):
                defaults = self._datas.get(key).get('defaults', {})
                if defaults:
                    self.logger.info("\t- %s" % key)
                    self.pre_config(defaults)
                    self.odoo_defaults(defaults)

    def odoo_defaults(self, defaults):
        if defaults:
            for default in defaults:
                self.logger.info("\t\t* %s" % default)
                default_value = defaults[default]['value']
                if type(default_value) is str and default_value.startswith('get_'):
                    default_value = self.safe_eval(default_value)
                self.execute_odoo('ir.default', 'set',
                                  [defaults[default]['model'],
                                   defaults[default]['field'],
                                   default_value,
                                   False, False, defaults[default].get('condition', False)], {'context': self._context})
