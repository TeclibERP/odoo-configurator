# -*- coding: utf-8 -*-
# Copyright (C) 2023 - Teclib'ERP (<https://www.teclib-erp.com>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from collections import OrderedDict
from . import base


class OdooConfig(base.OdooModule):
    _name = "Config"

    def apply(self):
        super(OdooConfig, self).apply()

        config_to_load = {}
        for key in self._datas:
            if isinstance(self._datas.get(key), dict) or isinstance(self._datas.get(key), OrderedDict):
                if self._datas.get(key).get('config', {}):
                    self.logger.info("\t- Config for %s" % key)
                    config_to_load.update(self._datas.get(key).get('config', {}))
        if config_to_load:
            self.pre_config(config_to_load)
            self.execute_config(config_to_load)

    def execute_config(self, config):
        config_id = self.execute_odoo('res.config.settings', 'create', [{}], {'context': self._context})
        self.execute_odoo('res.config.settings', 'write', [config_id, self.deep_convert_dict(config)],
                          {'context': self._context})
        self.execute_odoo('res.config.settings', 'execute', [config_id], {'context': self._context})
