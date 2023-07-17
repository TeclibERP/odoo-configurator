# -*- coding: utf-8 -*-
# Copyright (C) 2023 - Teclib'ERP (<https://www.teclib-erp.com>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import logging
import os.path
import sys

import hiyapyco

from .apps import connection
from .apps import account
from .apps import config
from .apps import datas
from .apps import defaults
from .apps import imports
from .apps import modules
from .apps import roles
from .apps import translations
from .apps import users
from .apps import website
from .apps import mattermost
from .apps import call
from .apps import import_configurator

from .import_manager import ImportManager
from .logging import get_logger
from .odoo_connection import OdooConnection
from .password_manager import PasswordManager

logger = get_logger(__name__)


class Configurator:
    mode = ["config"]
    debug = False

    def __init__(self, paths, install=False, update=False, debug=False, debug_xmlrpc=False, keepass=''):
        self.password_manager = PasswordManager(keepass)
        self.paths = paths
        self.configurator_dir = os.path.dirname(sys.argv[0])
        if install:
            self.mode.append('install')
        if update:
            self.mode.append('update')
        self.debug = debug
        self.debug_xmlrpc = debug_xmlrpc
        self.config, self.pre_update_config = self.parse_config()
        self.log_history = []
        if debug:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

        self.connection = False
        self.import_manager = False
        connection.OdooConnection(self).pre_config(self.config['auth']['odoo'])
        self.connection = OdooConnection(
            self.config['auth']['odoo']['url'],
            self.config['auth']['odoo']['dbname'],
            self.config['auth']['odoo']['username'],
            self.config['auth']['odoo']['password'],
            version=self.config.get('version', False),
            http_user=self.config['auth']['odoo'].get('http_user'),
            http_password=self.config['auth']['odoo'].get('http_password'),
            createdb=self.config['auth']['odoo'].get('create_db'),
            debug_xmlrpc=self.debug_xmlrpc,
        )
        self.import_manager = ImportManager(self)

    def parse_config(self):
        count_inherit = 0
        count_pre_update = 0
        pre_update_config = None
        parsed_config = hiyapyco.load(self.paths, method=hiyapyco.METHOD_MERGE, interpolate=True,
                                      failonmissingfiles=True,
                                      loglevel='INFO')

        while len(parsed_config.get("pre_update", [])) != count_pre_update:
            count_pre_update = len(parsed_config.get("pre_update", []))
            config_files = self.get_files_path(parsed_config['pre_update'])
            logger.info("Pre Update Loading %s" % (",".join(config_files)))
            pre_update_config = hiyapyco.load(config_files, method=hiyapyco.METHOD_MERGE, interpolate=True,
                                              failonmissingfiles=True, loglevel='INFO')
            pre_update_config['auth'] = parsed_config['auth']

        while len(parsed_config.get("inherits", [])) != count_inherit:
            count_inherit = len(parsed_config.get("inherits", []))
            config_files = self.paths + self.get_files_path(parsed_config['inherits']) + self.paths
            logger.info("Configuration Loading %s" % (",".join(config_files)))
            parsed_config = hiyapyco.load(config_files, method=hiyapyco.METHOD_MERGE, interpolate=True,
                                          failonmissingfiles=True, loglevel='INFO')

        parsed_config['scripts'] = []
        count_script = 0
        while len(parsed_config.get("script_files", [])) != count_script:
            count_script = len(parsed_config.get("script_files", []))
            script_files = self.get_files_path(parsed_config['script_files'])

            for script_file in script_files:
                parsed_script = hiyapyco.load(script_file, method=hiyapyco.METHOD_MERGE, interpolate=True,
                                              failonmissingfiles=True, loglevel='INFO')
                if parsed_script.get('title'):
                    parsed_script['title'] = '%s : %s' % (os.path.basename(script_file),
                                                          parsed_script.get('title'))
                else:
                    parsed_script['title'] = os.path.basename(script_file)
                parsed_config['scripts'].append(parsed_script)

        return parsed_config, pre_update_config

    def get_files_path(self, files):
        res = []
        template_dirs = [
            os.path.join(self.configurator_dir, 'templates'),
            os.path.join(self.configurator_dir, 'src/templates'),
            os.path.join(os.path.dirname(__file__), '../templates'),
        ]
        for file in files:
            if os.path.isfile(file):
                res.append(file)
            else:
                file_found = ''
                for template_dir in template_dirs:
                    file_path = os.path.join(template_dir, file)
                    if os.path.isfile(file_path):
                        file_found = file_path
                        res.append(file_path)
                        continue
                if file_found:
                    continue

                for path in self.paths:
                    file_path = os.path.join(os.path.dirname(path), file)
                    if os.path.isfile(file_path):
                        file_found = file_path
                        continue

                if file_found:
                    res.append(file_found)
                else:
                    logger.info("File not found: %s" % file)
        return res

    def get_log(self):
        return "\n".join(self.log_history)

    def show(self):
        pass
        # logger.info('show')
        # logger.info(pformat(self.config))

    def start(self):
        translations.OdooTranslations(self)
        modules_manager = modules.OdooModules(self)
        modules_manager.pre_update_config_modules()
        datas_manager = datas.OdooDatas(self)
        datas_manager.execute_pre_update_config_datas()
        modules_manager.install_config_modules()
        datas_manager.execute_update_config_datas()
        config.OdooConfig(self)
        roles.OdooRoles(self)
        defaults.OdooDefaults(self)
        users.OdooUsers(self)
        account.OdooAccount(self)
        website.OdooWebsite(self)
        imports.OdooImports(self)
        import_configurator.ImportConfigurator(self)
        mattermost.Mattermost(self)
        call.OdooCalls(self)
        return self.get_log()
