# -*- coding: utf-8 -*-
# Copyright (C) 2023 - Teclib'ERP (<https://www.teclib-erp.com>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from collections import OrderedDict
import os
import sys
from . import base


class OdooImports(base.OdooModule):
    _name = "Imports"

    def get_func(self, data):
        func = getattr(self._import_manager, 'import_csv')
        if data.get('specific_import', False):
            import importlib.util as ilu
            self.logger.info("Import specific import %s %s : %s" % (
                data.get('specific_import', False), data.get('specific_method', False), data.get('file_path', False)))
            path = os.path.join(os.path.dirname(sys.argv[1]), 'datas', data.get('specific_import', False))
            spec = ilu.spec_from_file_location('import_specific', path)
            specific_lib = ilu.module_from_spec(spec)
            spec.loader.exec_module(specific_lib)
            func = getattr(self._import_manager, data.get('specific_method', False))
        return func

    def apply(self):
        super(OdooImports, self).apply()
        datas = self._datas.get('import_data', {})
        if datas:
            self.logger.info("\t- %s" % "Global")
        for import_name in datas:
            if not self.install_mode() and datas[import_name].get('on_install_only', False):
                return
            import_data = datas[import_name]
            func = self.get_func(import_data)
            func(import_data.get('file_path', ''), import_data.get('model', ''), params=import_data)
        for key in self._datas:
            if isinstance(self._datas.get(key), dict) or isinstance(self._datas.get(key), OrderedDict):
                for key_import, data in self._datas.get(key, {}).get('import_data', {}).items():
                    self.logger.info("\t- %s" % key_import)
                    func = self.get_func(data)
                    func(data['file_path'], data['model'],
                         data.get('name_create_enabled_fields', False),
                         data.get('batch_size', 1000),
                         data.get('limit', 0),
                         datas[data].get('ignore_errors', []))
