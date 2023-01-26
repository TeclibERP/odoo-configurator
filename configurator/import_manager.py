# -*- coding: utf-8 -*-
# Copyright (C) 2023 - Teclib'ERP (<https://www.teclib-erp.com>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import csv
import os
import sys
from .logging import get_logger
from datetime import datetime
import unidecode
import re
from pprint import pformat

class ImportManager:

    def __init__(self, configurator):
        self.logger = get_logger("Imports ".ljust(15))
        self._connection = configurator.connection
        self._context_base = self._connection.context.copy()
        self._context_base.update({'tracking_disable': True, '__import__': True})
        self._context = self._context_base

        self.name_create_enabled_fields = ''
        self.context = False
        self.limit = 0
        self.skip_line = 0
        self.batch_size = 1000
        self.thread = 0
        self.ignore_errors = []

    @staticmethod
    def parse_csv_file(file_path, delimiter=","):
        vals = []
        with open(os.path.dirname(__file__) + '/' + file_path, 'r') as csvfile:
            reader = csv.reader(csvfile, skipinitialspace=True, delimiter=delimiter)
            next(reader)
            for line in reader:
                vals.append(line)
        return vals

    @staticmethod
    def clean_field(field):
        if "/" in field:
            field = field.split("/")[0]
        if "." in field:
            field = field.split(".")[0]
        return field

    @staticmethod
    def field_check_integer(field, data):
        if field['name'] == 'id':
            return data
        if not data:
            return data
        data = int(data)
        return data

    @staticmethod
    def field_check_float(field, data):
        if not data:
            return data
        if isinstance(data, str) and "," in data:
            data = data.replace(',', '.')
        data = float(data)
        return data

    @staticmethod
    def field_check_monetary(field, data):
        return ImportManager.field_check_float(field, data)

    @staticmethod
    def field_check_date(field, data):
        if not data:
            return data
        format_ok = False
        try:
            datetime.strptime(data, '%Y-%m-%d')
            format_ok = True
        except:
            format_ok = False
        if not format_ok:
            try:
                data = datetime.strptime(data, '%d/%m/%Y').strftime('%Y-%m-%d')
                format_ok = True
            except Exception as e:
                format_ok = False
        return data

    @staticmethod
    def field_check_datetime(field, data):
        if not data:
            return data
        format_ok = False
        try:
            datetime.strptime(data, '%Y-%m-%d %H:%M:%S')
            format_ok = True
        except Exception as e:
            format_ok = False
        if not format_ok:
            try:
                data = datetime.strptime(data, '%d/%m/%Y %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
                format_ok = True
            except Exception as e:
                format_ok = False
        if not format_ok:
            data = ImportManager.field_check_date(field, data)
            data += " 00:00:00"

        return data

    # @staticmethod
    def parse_csv_file_dictreader(self, file_path, fields, delimiter=","):
        vals = []
        new_file_path = ''
        if not os.path.isfile(file_path):
            new_file_path = os.path.dirname(__file__) + '/' + file_path
        if not os.path.isfile(new_file_path):
            new_file_path = os.path.join(os.path.dirname(sys.argv[1]), 'datas', file_path)
        if os.path.isfile(new_file_path):
            file_path = new_file_path
        else:
            print("ERROR: file %s not found." % file_path)
            return False


        with open(file_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile, skipinitialspace=True, delimiter=delimiter, quotechar='"')
            for i in range(self.skip_line):
                next(reader)
            cc = 0
            for line in reader:
                if self.limit and cc == self.limit:
                    break
                cc += 1
                for field in line:
                    clean_field = ImportManager.clean_field(field)
                    method = "field_check_%s" % (fields.get(clean_field,{}).get('ttype'))
                    if hasattr(ImportManager, method):
                        method_to_call = getattr(ImportManager, method)
                        line[field] = method_to_call(fields[clean_field], line[field])
                vals.append(line)


        return vals

    @staticmethod
    def name_to_xml_id(name):
        unaccented_string = unidecode.unidecode(name)
        return re.sub('[^A-Za-z0-9]+', '', unaccented_string).replace(' ', '_').lower()

    def load_batch(self, model, datas):
        if not datas:
            return
        cc_max = len(datas)
        start = datetime.now()

        load_keys = list(datas[0].keys())
        load_datas = [[]]
        cc = 0
        for data in datas:
            if len(load_datas[-1]) >= self.batch_size:
                load_datas.append([])
            cc += 1
            # print(load_keys)
            # print(data)
            load_datas[-1].append([data[i] for i in load_keys])

        cc = 0
        for load_data in load_datas:
            start_batch = datetime.now()
            self.logger.info("\t\t* %s : %s-%s/%s" % (model, self.skip_line + cc, self.skip_line + cc + len(load_data), self.skip_line + cc_max))
            cc += len(load_data)
            res = self._connection.execute_odoo(model, 'load', [load_keys, load_data], {'context': self._context})
            for message in res['messages']:
                if message.get('message'):
                    to_ignore = [ignore_error for ignore_error in self.ignore_errors if ignore_error in message['message']]
                else:
                    to_ignore = []
                if message.get('type') in ['warning', 'error']:
                    if not to_ignore:
                        if message.get('record'):
                            self.logger.error("record : %s" % (message['record']))
                        if message.get('message'):
                            self.logger.error("message : %s" % (message['message']))
                        # for l in load_data:
                        #     print("----")
                        #     for i in range(len(load_keys)):
                        #         print(i, load_keys[i],l[i])
                        raise Exception(message['message'])
                else:
                    self.logger.info(message)
            stop_batch = datetime.now()
            self.logger.info("\t\t\tBatch time %s ( %sms per object)" % (
                stop_batch - start_batch, ((stop_batch - start_batch) / len(load_data)).microseconds / 1000))

        stop = datetime.now()
        self.logger.info("\t\t\tTotal time %s" % (stop - start))

    def set_params(self, params):

        if not params:
            params = {
                'name_create_enabled_fields': "",
                'batch_size': 1000,
                'limit': 0,
                'skip_line': 0,
                'ignore_errors': [],
                'context': False}
        self.name_create_enabled_fields = params.get('name_create_enabled_fields')
        self.context = params.get('context', False)
        self.limit = params.get('limit', 0)
        self.skip_line = params.get('skip_line', 0)
        self.batch_size = params.get('batch_size', 1000)
        self.ignore_errors = params.get('ignore_errors', [])

        self._context = self._context_base.copy()
        if self.name_create_enabled_fields:
            create_enabled_fields = dict([x, 1] for x in set(self.name_create_enabled_fields.split(",")))
            self._context.update({'name_create_enabled_fields': create_enabled_fields})
        if self.context:
            self._context.update(self.context)

    def import_csv(self, file_path, model, params=dict):
        self.set_params(params)
        fields = self.get_model_fields(model)
        raw_datas = self.parse_csv_file_dictreader(file_path, fields)
        if raw_datas:
            self.load_batch(model, raw_datas)

    def get_model_fields(self, model):
        return {i['name']: i for i in self._connection.execute_odoo("ir.model.fields", 'search_read',
                                                                    [[('model', '=', model)],
                                                                     ['name', 'ttype', 'display_name']],
                                                                    {'context': self._context})}
