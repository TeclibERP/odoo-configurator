# -*- coding: utf-8 -*-
# Copyright (C) 2023 - Teclib'ERP (<https://www.teclib-erp.com>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import base64
import logging
import os.path
import sys
import pickle
import ssl
import xmlrpc.client
from pprint import pformat
from .logging import get_logger

import requests
from bs4 import BeautifulSoup

CACHE = "/tmp/.configurator_cache"

METHODE_MAPPING = {
    15: [('get_object_reference', 'check_object_reference')]
}

class OdooConnection:
    _context = {'lang': 'fr_FR', 'noupdate': True}
    _cache = {}

    def __init__(self, url, dbname, user, password, version=False, http_user=None, http_password=None, createdb=False,
                 debug_xmlrpc=False):
        self.logger = get_logger("Odoo Connection".ljust(15))
        if debug_xmlrpc:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
        self._url = url
        self._dbname = dbname
        self._user = user
        self._password = password
        self._http_user = http_user
        self._http_password = http_password
        self._version = version
        # noinspection PyProtectedMember,PyUnresolvedReferences
        self._insecure_context = ssl._create_unverified_context()
        self._load_cache()
        self._compute_url()
        if createdb:
            self._create_db()
        self._prepare_connection()

    @property
    def context(self):
        return self._context

    def _load_cache(self):
        self._cache = {}
        if os.path.isfile(CACHE):
            with open(CACHE, "rb") as f:
                self._cache = pickle.loads(f.read())

    def _save_cache(self):
        with open(CACHE, "wb") as f:
            f.write(pickle.dumps(self._cache))

    def _compute_url(self):
        if self._http_user or self._http_password:
            self._url = self._url.replace('https://', 'https://%s:%s@' % (self._http_user, self._http_password))

    def _get_xmlrpc_method(self, method):
        new_method = method
        for v in METHODE_MAPPING:
            if self._version >= v:
                for i in METHODE_MAPPING[v]:
                    if i[0] == method:
                        new_method = i[1]
        return new_method

    def _create_db(self):
        post = {
            'master_pwd': "admin123",
            'name': self._dbname,
            'login': self._user,
            'password': self._password,
            'phone': '',
            'lang': 'fr_FR',
            'country_code': 'fr',
        }
        session = requests.Session()
        session.verify = False
        r = session.post(url=self._url + "/web/database/create", params=post)
        soup = BeautifulSoup(r.text, 'html.parser')
        alert = soup.find('div', attrs={"class": u"alert alert-danger"})
        if alert:
            self.logger.debug(self._url + "/web/database/create")
            self.logger.debug(post)
            self.logger.debug(alert.get_text())
            if "already exists" not in alert.text:
                raise Exception(alert.text)

    def _prepare_connection(self):
        self.logger.info("Prepare connection %s %s %s" % (self._url, self._dbname, self._user))
        self.common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(self._url), allow_none=True,
                                                context=self._insecure_context)
        self.object = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(self._url), allow_none=True,
                                                context=self._insecure_context)
        self.uid = self.common.authenticate(self._dbname, self._user, self._password, {})
        self.logger.debug('Connection uid : %s' % self.uid)
        if not self.uid:
            raise Exception("Connection Error to %s %s %s" % (self._url, self._dbname, self._user))

    def execute_odoo(self, *args, no_raise=False, retry=0):
        self.logger.debug("*" * 50)
        self.logger.debug("Execute odoo :")
        self.logger.debug("\t Model : %s" % (args[0]))
        self.logger.debug("\t Method : %s" % (args[1]))
        self.logger.debug("\t " + "%s " * (len(args) - 2) % args[2:])
        self.logger.debug("*" * 50)
        try:
            res = self.object.execute_kw(self._dbname, self.uid, self._password, *args)
            return res
        except Exception as e:
            if no_raise:
                return
            if retry <= 3:
                return self.execute_odoo(*args, retry=retry+1)
            else:
                self.logger.error(pformat(args))
                if isinstance(e, xmlrpc.client.Fault):
                    self.logger.error(e.faultString, exc_info=True)
                else:
                    self.logger.error(e)
                raise e

    def get_ref(self, external_id):
        res = self.execute_odoo('ir.model.data',
                                self._get_xmlrpc_method('get_object_reference'),
                                external_id.split('.'))[1]
        self.logger.debug('Get ref %s > %s' % (external_id, res))
        return res

    def get_image_url(self, url):
        if 'image_url' not in self._cache:
            self._cache['image_url'] = {}
        if url not in self._cache['image_url']:
            self._cache['image_url'][url] = base64.b64encode(requests.get(url).content).decode("utf-8", "ignore")
            self._save_cache()
        return self._cache['image_url'][url]

    def get_image_local(self, path):
        if 'path' not in self._cache:
            self._cache['path'] = {}
        if not os.path.isfile(path):
            path = os.path.join(os.path.dirname(sys.argv[1]), 'datas', path)

        if path not in self._cache['path']:

            self._cache['path'][path] = base64.b64encode(open(path, "rb").read()).decode("utf-8", "ignore")
            self._save_cache()
        return self._cache['path'][path]

    @staticmethod
    def get_local_file(path, encode=False):
        if encode:
            with open(path, "rb") as f:
                res = f.read()
            res = base64.b64encode(res).decode("utf-8", "ignore")
        else:
            with open(path, "r") as f:
                res = f.read()
        return res

    def get_country(self, code):
        return self.execute_odoo('res.country', 'search', [[('code', '=', code)], 0, 1, "id", False],
                                 {'context': self._context})[0]

    def get_menu(self, website_id, url):
        return self.execute_odoo('website.menu', 'search',
                                 [[('website_id', '=', website_id), ('url', '=', url)], 0, 1, "id", False],
                                 {'context': self._context})[0]

    def get_search_id(self, model, domain, order='asc'):
        res = self.execute_odoo(model, 'search', [domain, 0, 1, "id %s" % order, False], {'context': self._context})
        return res[0] if res else False

    def get_id_from_xml_id(self, xml_id, no_raise=False):
        if '.' not in xml_id:
            xml_id = "external_config." + xml_id
        try:
            object_reference = self._get_xmlrpc_method('get_object_reference')
            res_object_reference = self.execute_odoo('ir.model.data', object_reference, xml_id.split('.'),
                                                     {'context': {'active_test': False}}, no_raise=True)
            return res_object_reference[1] if res_object_reference else False
        except Exception as e:  # TODO : get true exception type and return False
            if no_raise:
                pass
            else:
                raise e

    def get_xml_id_from_id(self, model, res_id):
        try:
            domain = [('model', '=', model), ('res_id', '=', res_id)]
            res = self.execute_odoo('ir.model.data', 'search_read', [domain, ['module', 'name'], 0, 0, "id"],
                                    {'context': self._context})[0]
            return "%s.%s" % (res['module'], res['name'])
        except Exception as e:  # TODO : get true exception type and return False
            raise e
            # return False

    def set_active(self, is_active, model, domain, search_value_xml_id):
        if search_value_xml_id:
            object_id = self.get_id_from_xml_id(search_value_xml_id)
            domain = [(domain[0][0], domain[0][1], object_id)]
        object_ids = self.execute_odoo(model, 'search', [domain, 0, 0, "id", False], {'context': self._context})
        self.execute_odoo(model, 'write', [object_ids, {'active': is_active}], {'context': self._context})

    def read_search(self, model, domain, context=False):
        res = self.execute_odoo(model, 'search_read',
                                [domain],
                                {'context': context or self._context})
        return res
