# -*- coding: utf-8 -*-
# Copyright (C) 2023 - Teclib'ERP (<https://www.teclib-erp.com>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from . import base


class OdooUsers(base.OdooModule):
    _name = "Users"
    _key = "users"

    def apply(self):
        super(OdooUsers, self).apply()

        users = self._datas.get(self._key, {}).get('datas', {})
        for user in users:
            groups_id = []
            for group in users[user].get("groups_id", []):
                if group == "unlink all":
                    groups_id.append((5,))
                else:
                    groups_id.append(
                        (4, self._connection.get_ref(group)))

            vals = {
                'login': users[user]['values'].get("login"),
                'groups_id': groups_id,
            }
            self._context['active_test'] = False
            user_id = self.execute_odoo('res.users', 'search', [[('login', '=', vals['login'])], 0, 0, "id", False],
                                        {'context': self._context})
            if not user_id:
                self.execute_odoo('res.users', 'create', [vals], {'context': self._context})
            else:
                self.execute_odoo('res.users', 'write', [user_id, vals], {'context': self._context})
