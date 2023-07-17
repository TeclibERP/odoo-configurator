# -*- coding: utf-8 -*-
# Copyright (C) 2023 - Teclib'ERP (<https://www.teclib-erp.com>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from collections import OrderedDict
import requests
from ast import literal_eval
from zipfile import ZipFile
import os
from . import base


class ImportConfigurator(base.OdooModule):
    _name = "Import Configurator"

    def apply(self):
        super(ImportConfigurator, self).apply()
        for key in self._datas:
            if isinstance(self._datas.get(key), dict) or isinstance(self._datas.get(key), OrderedDict):
                action_name = 'import_configurator'
                import_configurator = self._datas.get(key).get(action_name, {})
                if import_configurator:

                    self.logger.info("\t- %s : %s" % (key, action_name))
                    res = self.execute_odoo('ir.config_parameter', 'search_read',
                                            [[('key', '=', 'odoo_configurator.access.token')],
                                             ['value']],
                                            {'context': self._context})
                    if res:
                        token = res[0].get('value', False)
                        s = requests.Session()
                        s.get(url='%s/web?db=%s' % (self._configurator.connection._url,
                                                    self._configurator.connection._dbname))

                        url = '%s/teclib_configurator_generator/get_configuration/%s' % \
                              (self._configurator.connection._url, token)
                        r = s.get(url=url)

                        open('odoo_configurator.zip', 'wb').write(r.content)
                        dest_path = os.path.dirname(self._configurator.paths[0])+'/config'
                        with ZipFile('odoo_configurator.zip', 'r') as zip:
                            zip_files = zip.namelist()
                            for export_file in import_configurator:
                                for zip_file in zip_files:
                                    if zip_file.endswith('/'+export_file) and '/modules/' in zip_file:
                                        file_bin = zip.read(zip_file)
                                        open(dest_path+'/'+export_file, 'wb').write(file_bin)
                                        self.logger.info("\t\t--> %s Updated" % export_file)

                #######################
                #  CONFIGURATOR FILE  #
                #######################
                action_name = 'import_configurator_model_file'
                configurator_model_files = self._datas.get(key).get(action_name, {})
                if configurator_model_files:

                    self.logger.info("\t- %s : %s" % (key, action_name))
                    res = self.execute_odoo('ir.config_parameter', 'search_read',
                                            [[('key', '=', 'odoo_configurator.access.token')],
                                             ['value']],
                                            {'context': self._context})
                    if res:
                        token = res[0].get('value', False)
                        s = requests.Session()
                        s.get(url='%s/web?db=%s' % (self._configurator.connection._url,
                                                    self._configurator.connection._dbname))

                        for configurator_model_file in configurator_model_files:
                            model_file = literal_eval(configurator_model_file)
                            if isinstance(model_file, str):
                                model = model_file
                                domain = '[]'
                                fields = '[]'
                            else:
                                model = model_file[0]
                                domain = str(model_file[1]) if len(model_file) > 1 else '[]'
                                fields = str(model_file[2]) if len(model_file) > 2 else '[]'
                            name = model.replace('.', '_')
                            dest_path = os.path.dirname(self._configurator.paths[0]) + '/config'
                            url = '%s/teclib_configurator_generator/get_configuration_file/%s' % \
                                  (self._configurator.connection._url, token)
                            r = s.get(url=url, params={'domain': domain, 'model': model, 'fields': fields})
                            open('%s/%s.yml' % (dest_path, name), 'wb').write(r.content)

                ##############################
                #  CONFIGURATOR BINARY FILE  #
                ##############################
                action_name = 'import_configurator_binary_file'
                configurator_model_files = self._datas.get(key).get(action_name, {})
                if configurator_model_files:
                    res = self.execute_odoo('ir.config_parameter', 'search_read',
                                            [[('key', '=', 'odoo_configurator.access.token')],
                                             ['value']],
                                            {'context': self._context})
                    if res:
                        token = res[0].get('value', False)
                    else:
                        return
                    url = '%s/teclib_configurator_generator/get_binary_file/%s' % \
                          (self._configurator.connection._url, token)
                    self.logger.info("\t- %s : %s" % (key, action_name))
                    res = self.execute_odoo('ir.config_parameter', 'search_read',
                                            [[('key', '=', 'odoo_configurator.access.token')],
                                             ['value']],
                                            {'context': self._context})
                    if res:
                        token = res[0].get('value', False)
                        s = requests.Session()
                        s.get(url='%s/web?db=%s' % (self._configurator.connection._url,
                                                    self._configurator.connection._dbname))

                        for configurator_model_file in configurator_model_files:
                            model_file = literal_eval(configurator_model_file)
                            model = model_file[0]
                            field = model_file[1]
                            res_ids = model_file[2]
                            for res_id in res_ids:
                                dest_path = os.path.dirname(self._configurator.paths[0]) + '/datas'

                                r = s.get(url=url, params={'model': model, 'field': field, 'res_id': res_id})

                                if r.headers['content-disposition']:
                                    file_name = r.headers['content-disposition'].split('=')[1].split("''")[1]
                                else:
                                    file_name = '%s_%s.bin' % (model.replace('.', '_'), res_id)
                                open('%s/%s' % (dest_path, file_name), 'wb').write(r.content)
