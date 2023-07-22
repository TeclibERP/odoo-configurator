# -*- coding: utf-8 -*-
# Copyright (C) 2023 - Teclib'ERP (<https://www.teclib-erp.com>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from collections import OrderedDict
from ast import literal_eval

from . import base
from .config import OdooConfig


def prepare_load_values(load_fields, fields, values):
    load_values = []
    for load_field in load_fields:
        if load_field in fields:
            value = values[fields.index(load_field)]
        else:
            value = False
        load_values.append(value)

    return load_values


class OdooDatas(base.OdooModule):
    _name = "Datas"

    def apply(self):
        pass  # For remove standard log

    def execute(self, datas):
        for key in datas:
            if isinstance(datas.get(key), dict) or isinstance(datas.get(key), OrderedDict):
                data = datas.get(key).get('datas', {})
                if data:
                    self.logger.info("\t- %s" % key)
                    self.odoo_datas(data)

        scripts = datas.get('scripts', [])
        odoo_config = OdooConfig(self._configurator)
        for script in scripts:
            self.logger.info("Script - %s" % script.get('title'))
            odoo_config.execute_script_config(script)
            self.execute(script)

    def execute_pre_update_config_datas(self):
        self.logger.info("Apply Pre-%s" % self._name)
        if self._pre_datas:
            self.execute(self._pre_datas)

    def execute_update_config_datas(self):
        self.logger.info("Apply %s" % self._name)
        self.get_external_config_xmlid_cache()
        self.execute(self._datas)

    def get_external_config_xmlid_cache(self):
        domain = [['module', '=', 'external_config']]
        datas = self.execute_odoo('ir.model.data', 'search_read', [domain, ['name', 'res_id']], {'context': {}})
        for data in datas:
            self._configurator.xmlid_cache['external_config.%s' % data['name']] = data['res_id']

    def execute_config(self, config):
        if config:
            self.pre_config(config)
            self._connection.execute_config(config)

    def odoo_datas(self, datas):
        self.pre_config(datas)
        raw_load_values = []
        load_fields = []
        load = datas.pop('load', False)
        model = datas.pop('model', False)
        for data in datas:
            object_ids = False
            self.logger.info("\t\t* %s" % data)
            if not isinstance(datas[data], dict):
                return
            if 'install' not in self._mode and datas[data].get('on_install_only', False):
                return
            model = datas[data].get('model') or model
            key = datas[data].get('key', False)
            force_id = datas[data].get('force_id', False)
            delete_all = datas[data].get('delete_all', False)
            delete_domain = datas[data].get('delete_domain', False)
            delete_id = datas[data].get('delete_id', False)
            deactivate = datas[data].get('deactivate', False)
            activate = datas[data].get('activate', False)
            update_domain = datas[data].get('update_domain', False)
            search_value_xml_id = datas[data].get('search_value_xml_id', False)
            action_server_id = datas[data].get('action_server_id', False)
            function = datas[data].get('function', False)
            no_raise = datas[data].get('no_raise', False)
            context = dict(datas[data].get('context', {}))
            values = datas[data].get('values', {})
            languages = datas[data].get('languages', [self._context['lang']])

            # escape {{
            for val_key in values:
                val = values[val_key]
                if isinstance(val, str) and '\\{\\{' in val:
                    values[val_key] = val.replace('\\{\\{', '{{')

            config_context = self._context.copy()
            config_context.update(context)

            if delete_all or delete_domain:
                if 'install' not in self._mode and datas[data].get('on_install_only', False):
                    continue
                if delete_domain:
                    domain = self.eval_param_value(delete_domain)
                else:
                    domain = []
                object_ids = self.execute_odoo(model, 'search', [domain, 0, 0, "id", False],
                                               {'context': config_context})
                for object_id in object_ids:
                    self.execute_odoo(model, 'unlink', [object_id])
                continue

            if delete_id:
                try:
                    object_id = self._connection.get_id_from_xml_id(delete_id, no_raise=True)
                    if object_id:
                        self.execute_odoo(model, 'unlink', [object_id])
                except Exception as e:
                    self.logger.error(e)
                    pass
                continue

            if update_domain:
                domain = self.eval_param_value(update_domain)
                if search_value_xml_id:
                    object_id = self._connection.get_id_from_xml_id(search_value_xml_id)
                    domain = [(domain[0][0], domain[0][1], object_id)]
                object_ids = self.execute_odoo(model, 'search', [domain, 0, 0, "id", False],
                                               {'context': config_context})
                self.logger.debug("Update Domain %s %s" % (len(object_ids), model))
                self.execute_odoo(model, 'write', [object_ids, dict(values)], {'context': config_context})
                continue

            if deactivate:
                self._connection.set_active(False, model, literal_eval(deactivate), search_value_xml_id)
                continue

            if activate:
                self._connection.set_active(True, model, literal_eval(activate), search_value_xml_id)
                continue

            if key:
                object_ids = self.execute_odoo(model, 'search',
                                               [[(key, '=', values[key])], 0, 0, "id", False],
                                               {'context': config_context})
            elif force_id:
                if load:
                    values['id'] = force_id
                else:
                    values, object_ids = self.set_force_id(model, values, config_context, force_id)
            elif action_server_id:
                self.exec_action_server(action_server_id, datas[data], config_context, no_raise)
                continue
            elif function:
                self.exec_function(function, datas[data], config_context, no_raise)
                continue
            else:
                self.logger.error("key=%s", key)
                raise

            # prepare many2many list of xmlid
            for key in values.keys():
                if isinstance(values[key], list) and '/id' in key:
                    if values[key] and isinstance(values[key][0], str) and '.' in values[key][0]:
                        values[key] = ','.join(values[key])

            if load:

                fields, rec_values = self.save_values(model, values, config_context, force_id, object_ids,
                                                      load_batch=load)
                load_fields = list(set(load_fields + fields))
                raw_load_values.append((fields, rec_values[0]))
            else:
                for language in languages:
                    config_context['lang'] = language
                    self.save_values(model, values, config_context, force_id, object_ids)

        if load:
            load_values = [prepare_load_values(load_fields, v[0], v[1]) for v in raw_load_values]
            context = self._context
            self.execute_load(model, load_fields, load_values, context)

    def save_values(self, model, values, config_context, force_id, object_ids, load_batch=False):
        if not force_id or isinstance(force_id, int):
            if object_ids:
                self.execute_odoo(model, 'write', [object_ids, dict(values)], {'context': config_context})
            else:
                self.execute_odoo(model, 'create', [dict(values)], {'context': config_context})
        else:
            load_keys = list(values.keys())
            load_data = [[]]
            for i in load_keys:
                if isinstance(values[i], bool):
                    load_data[0].append(str(values[i]))
                else:
                    load_data[0].append(values[i])
            self.logger.debug('%s: %s %s' % (model, load_keys, load_data))
            if load_batch:
                return load_keys, load_data
            else:
                self.execute_load(model, load_keys, load_data, config_context)

    def execute_load(self, model, load_keys, load_data, config_context):
        res = self.execute_odoo(model, 'load', [load_keys, load_data], {'context': config_context})
        for message in res['messages']:
            self.logger.error("%s : %s" % (message['record'], message['message']))

    def set_force_id(self, model, values, config_context, force_id=False):
        if isinstance(force_id, int):
            values['id'] = force_id
            object_ids = self.execute_odoo(model, 'search', [[('id', '=', force_id)], 0, 0, "id", False],
                                           {'context': config_context})
        else:
            if '.' not in force_id:
                force_id = "external_config." + force_id
            values['id'] = force_id
            if force_id in self._configurator.xmlid_cache:
                return values, self._configurator.xmlid_cache[force_id]
            module, name = force_id.split('.')
            if self.execute_odoo('ir.model.data', 'search',
                                 [[('module', '=', module), ('name', '=', name)], 0, 0, "id", False],
                                 {'context': config_context}):
                object_ids = self._connection.get_ref(force_id)
            else:
                object_ids = []
        return values, object_ids

    def exec_action_server(self, action_server_id, datas, context, no_raise):
        context.update({'active_model': datas.get('model'),
                        'active_id': datas.get('res_id')})
        res = self.execute_odoo('ir.actions.server', 'run', [action_server_id], {'context': context},
                                no_raise=no_raise)

    def eval_param_value(self, param):
        if isinstance(param, str):
            if param.startswith('get_'):
                return self.safe_eval(param)
            if param[0] in ['[', '{', '(']:
                param_val = literal_eval(param)
                return param_val

        if isinstance(param, OrderedDict):
            return dict(param)
        if isinstance(param, list):
            param_val = []
            for param_el in param:
                param_el_val = self.eval_param_value(param_el)
                param_val.append(param_el_val)
            return param_val

        return param

    def exec_function(self, function, datas, context, no_raise):
        params = datas.get('params')
        if params:
            res_id = datas.get('res_id', False)
            function_params = [res_id] if res_id else [0]
            for param in params:
                param_val = self.eval_param_value(param)
                function_params.append(param_val)

            extra_params = {'context': context}
            kw = datas.get('kw')
            if kw:
                extra_params.update(dict(kw))

            res = self.execute_odoo(datas.get('model'), function, function_params, extra_params,
                                    no_raise=no_raise)
        else:
            res = self.execute_odoo(datas.get('model'), function, [datas.get('res_id')], {'context': context},
                                    no_raise=no_raise)
