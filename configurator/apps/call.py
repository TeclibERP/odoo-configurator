# -*- coding: utf-8 -*-
# Copyright (C) 2023 - Teclib'ERP (<https://www.teclib-erp.com>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from . import base
from collections import OrderedDict


class OdooCalls(base.OdooModule):
    _name = "Calls"
    _key = "call"

    def apply(self):
        super(OdooCalls, self).apply()
        calls = []
        for key in self._datas:
            if isinstance(self._datas.get(key), dict) or isinstance(self._datas.get(key), OrderedDict):
                if self._datas.get(key).get(self._key, {}):
                    calls = {}
                    for call in self._datas.get(key).get(self._key, {}):
                        print(self.install_mode() , self._datas.get(key).get(self._key, {}).get(call).get(
                            'on_install_only', False))
                        if not self.install_mode() and self._datas.get(key).get(self._key, {}).get(call).get('on_install_only', False):
                            pass
                        else:
                            calls[call] = self._datas.get(key).get(self._key, {}).get(call)

        for call in calls:
            call_name = call
            call = calls[call]
            context = self._context
            context.update(call.get('context',{}))
            if call.get('model',{}) and call.get('method',{}):
                args = call.get('args',[])
                args_ok = []
                for i in args or []:
                    if isinstance(i,OrderedDict):
                        args_ok.append(dict(i))
                    else:
                        args_ok.append(i)
                self.logger.info('\t- Execute %s : env[\'%s\'].%s(%s,context=%s)' % (call_name, call.get('model', {}), call.get('method', {}), args_ok,call.get('context', {})))
                res = self.execute_odoo(call.get('model',{}), call.get('method',{}), args_ok, {'context': context})
                self.logger.info('\t- Call result %s' % (res))
            else:
                self.logger.info('\t- Call error %s' % (call_name))

