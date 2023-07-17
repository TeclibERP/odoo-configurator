# -*- coding: utf-8 -*-
# Copyright (C) 2023 - Teclib'ERP (<https://www.teclib-erp.com>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import time
from collections import OrderedDict

from . import base


class OdooModules(base.OdooModule):
    _name = "Modules"
    _modules_cache = {}
    _modules_updated = False
    _modules_theme_cache = {}
    _uninstalled_modules_cache = {}

    def apply(self):
        pass  # For remove standard log

    def pre_update_config_modules(self):
        if self._pre_datas:
            self.install_modules(self._pre_datas)
            self.update_modules(self._pre_datas)
            self.uninstall_modules(self._pre_datas)

    def install_config_modules(self):
        self.install_modules(self._datas)
        self.update_modules(self._datas)
        self.uninstall_modules(self._datas)

    def install_modules(self, config):
        self.logger.info("Install modules")
        self.install_odoo(config.get('modules', []))
        for key in config:
            if isinstance(config.get(key), dict) or isinstance(config.get(key), OrderedDict):
                modules = config.get(key).get('modules', [])
                if modules:
                    self.logger.info("\t- Modules for %s" % key)
                    self.install_odoo(modules)

    def update_modules(self, config):
        self.logger.info("Update modules")

        self.update_module_odoo(config.get('updates', []))
        for key in config:
            if isinstance(config.get(key), dict) or isinstance(config.get(key), OrderedDict):
                modules = config.get(key).get('updates', [])
                if modules:
                    self.logger.info("\t- Modules for %s" % key)
                    self.update_module_odoo(modules)

    def uninstall_modules(self, config):
        self.logger.info("Uninstall modules")

        self.uninstall_odoo(config.get('uninstall_modules', []))
        for key in config:
            if isinstance(config.get(key), dict) or isinstance(config.get(key), OrderedDict):
                modules = config.get(key).get('uninstall_modules', [])
                if modules:
                    self.logger.info("\t- Uninstall Modules for %s" % key)
                    self.uninstall_odoo(modules)

    def update_list(self):
        if not self._modules_updated:
            self.execute_odoo('ir.module.module', 'update_list', [])
            self._modules_updated = True
        return {i['name']: {'state': i['state'], 'id': i['id']} for i in
                self.execute_odoo('ir.module.module', 'search_read',
                                  [[], ['name', 'state'], 0, 0, "id"],
                                  {'context': self._context})}

    def install_odoo(self, modules):
        if not self._modules_cache:
            self._modules_cache = self.update_list()

        if modules:
            to_install = []
            missing_modules = []
            for module in modules:
                self.logger.info('\t\t* %s' % module)
                if self._modules_cache.get(module):
                    if self._modules_cache.get(module).get('state') != 'installed':
                        to_install.append(self._modules_cache.get(module).get('id'))
                else:
                    missing_modules.append(module)

            if missing_modules:
                self.logger.error("\t\tModules not found : %s " % (", ".join(missing_modules)))

            if to_install:
                self.execute_odoo('ir.module.module', 'button_immediate_install', [to_install])

    def update_module_odoo(self, modules):
        if modules:
            self.logger.info('\t\tUpdate %s', modules)
            self.execute_odoo('ir.module.module', 'button_immediate_upgrade',
                              [[self._connection.get_id_from_xml_id("base.module_" + m) for m in modules]])

    def uninstall_odoo(self, modules):
        if not self._uninstalled_modules_cache:
            self._uninstalled_modules_cache = self.update_list()

        if modules:
            to_uninstall = []
            for module in modules:
                self.logger.info('\t\t* %s' % module)
                if self._uninstalled_modules_cache.get(module).get('state') != 'uninstalled':
                    to_uninstall.append(self._modules_cache.get(module).get('id'))

            for m in to_uninstall:
                self.execute_odoo('ir.module.module', 'button_immediate_uninstall', [m], no_raise=True)
                time.sleep(3)

    def install_odoo_theme(self, module):
        if not self._modules_theme_cache:
            self.update_list()
            self._modules_theme_cache = {i['name']: {'state': i['state'], 'is_installed_on_current_website': i[
                'is_installed_on_current_website'], 'id': i['id']} for i in
                                         self.execute_odoo('ir.module.module', 'search_read',
                                                           [[], ['name', 'state', 'is_installed_on_current_website'], 0,
                                                            0, "id"], {'context': self._context})}

        if module:
            if not self._modules_theme_cache.get(module).get('is_installed_on_current_website'):
                self.execute_odoo('ir.module.module', 'button_choose_theme',
                                  [[self._modules_theme_cache.get(module).get('id')]])
