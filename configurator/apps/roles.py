# -*- coding: utf-8 -*-
# Copyright (C) 2023 - Teclib'ERP (<https://www.teclib-erp.com>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from collections import OrderedDict

from . import base


class OdooRoles(base.OdooModule):
    _name = "Roles"

    def apply(self):
        super(OdooRoles, self).apply()

        for key in self._datas:
            if isinstance(self._datas.get(key), dict) or isinstance(self._datas.get(key), OrderedDict):
                for key_import, data in self._datas.get(key, {}).get('datas_roles', {}).items():
                    self.logger.info("\t- %s" % key_import)
                    force_id = data.get('force_id', False)
                    role_name = data['values'].get("name")
                    role_id = self.execute_odoo('res.users.role', 'search',
                                                [[('name', '=', role_name)], 0, 0, "id", False],
                                                {'context': self._context})
                    implied_ids = [(5,), ]
                    for group in data['values'].get("implied_ids"):
                        implied_ids.append(
                            (4, self._connection.get_ref(group)))

                    user_ids = []
                    for user in data['values'].get("line_ids", []):
                        user_ids.append(
                            (4, self._connection.get_ref(user)))

                    vals = {
                        'id': force_id,
                        'name': role_name,
                        'implied_ids': implied_ids,
                        'line_ids': user_ids,
                    }
                    if not role_id:
                        self.execute_odoo('res.users.role', 'create', [vals], {'context': self._context})
                    else:
                        self.execute_odoo('res.users.role', 'write', [role_id, vals], {'context': self._context})
