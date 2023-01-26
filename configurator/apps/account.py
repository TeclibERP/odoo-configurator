# -*- coding: utf-8 -*-
# Copyright (C) 2023 - Teclib'ERP (<https://www.teclib-erp.com>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from . import base


class OdooAccount(base.OdooModule):
    _name = "Account"
    _key = "account"

    def apply(self):
        super(OdooAccount, self).apply()

        first = True
        banks = self._datas.get(self._key, {}).get('data', {}).get('banks', [])
        for bank in banks:
            # Create or update bank
            vals = {
                'name': bank,
                'bic': banks.get(bank).get("bic", ""),
                'street': banks.get(bank).get("street", ""),
                'street2': banks.get(bank).get("street2", ""),
                'city': banks.get(bank).get("city", ""),
                'zip': banks.get(bank).get("zip", ""),
                'country': self.execute_odoo('res.country', 'search',
                                             [[('code', '=', banks.get(bank)["country_code"])], 0, 0, "id", False],
                                             {'context': self._context})[0],
                'phone': banks.get(bank).get("phone", ""),
                'email': banks.get(bank).get("email", ""),
            }
            bank_id = self.execute_odoo('res.bank', 'search', [[('bic', '=', vals["bic"])], 0, 0, "id", False],
                                        {'context': self._context})
            if not bank_id:
                bank_id = self.execute_odoo('res.bank', 'search', [[('name', '=', vals["name"])], 0, 0, "id", False],
                                            {'context': self._context})
                if not bank_id:
                    bank_id = self.execute_odoo('res.bank', 'create', [vals], {'context': self._context})
                else:
                    self.execute_odoo('res.bank', 'write', [bank_id, vals], {'context': self._context})
                    bank_id = bank_id[0]
            else:
                self.execute_odoo('res.bank', 'write', [bank_id, vals], {'context': self._context})
                bank_id = bank_id[0]

            # Create or update partner bank
            vals = {
                'acc_number': banks.get(bank).get("iban", ""),
                'partner_id': 1,
                'bank_id': bank_id,
            }
            partner_bank_id = self.execute_odoo('res.partner.bank', 'search',
                                                [[('acc_number', '=', vals["acc_number"])], 0, 0, "id", False],
                                                {'context': self._context})
            if not partner_bank_id:
                partner_bank_id = self.execute_odoo('res.partner.bank', 'create', [vals], {'context': self._context})
            else:
                self.execute_odoo('res.partner.bank', 'write', [partner_bank_id, vals], {'context': self._context})
                partner_bank_id = partner_bank_id[0]

            # Check default journal exist
            default_journal_id = self.execute_odoo('account.journal', 'search',
                                                   [[('name', '=', 'Banque')], 0, 0, "id", False],
                                                   {'context': self._context})
            journal_id = False
            if first:
                first = False
                if default_journal_id:
                    journal_id = default_journal_id

            # Create or update journal
            vals = {
                'name': banks.get(bank).get("journal_name", ""),
                'code': banks.get(bank).get("code", ""),
                'bank_account_id': partner_bank_id,
                'type': 'bank',
            }
            if not journal_id:
                journal_id = self.execute_odoo('account.journal', 'search',
                                               [[('bank_account_id', '=', vals['bank_account_id'])], 0, 0, "id", False],
                                               {'context': self._context})
            if not len(journal_id):
                journal_id = self.execute_odoo('account.journal', 'create', [vals], {'context': self._context})
            else:
                self.execute_odoo('account.journal', 'write', [journal_id, vals], {'context': self._context})
                journal_id = journal_id[0]

            # Update account
            account_id = self.execute_odoo('account.journal', 'read', [journal_id, ['default_debit_account_id']],
                                           {'context': self._context})[0]['default_debit_account_id'][0]
            self.execute_odoo('account.account', 'write', [account_id, {'name': vals["name"]}],
                              {'context': self._context})

        # # ##########################################################################################################
        # # JOURNAL
        # # ##########################################################################################################
        # sale_journal_id = self.execute_odoo('account.journal', 'search',
        #                                     [[('name', '=', "Factures clients")], 0, 0, "id", False],
        #                                     {'context': self._context})
        # sale_journal = \
        # self.execute_odoo('account.journal', 'read', [sale_journal_id, ['sequence_id', 'refund_sequence_id']],
        #                   {'context': self._context})[0]
        # if config.get(key, {}).get('data', {}).get('invoice', ""):
        #     self.execute_odoo('ir.sequence', 'write', [sale_journal['sequence_id'][0], {
        #         'prefix': config.get(key, {}).get('data', {}).get('invoice', "")}], {'context': context})
        # if config.get(key, {}).get('data', {}).get('refund', ""):
        #     self.execute_odoo('ir.sequence', 'write', [sale_journal['refund_sequence_id'][0], {
        #         'prefix': config.get(key, {}).get('data', {}).get('refund', "")}], {'context': context})
        #
        # purchase_journal_id = self.execute_odoo('account.journal', 'search',
        #                                         [[('name', '=', "Factures fournisseurs")], 0, 0, "id", False],
        #                                         {'context': self._context})
        # purchase_journal = \
        # self.execute_odoo('account.journal', 'read', [purchase_journal_id, ['sequence_id', 'refund_sequence_id']],
        #                   {'context': self._context})[0]
        # if config.get(key, {}).get('data', {}).get('supplier_invoice', ""):
        #     self.execute_odoo('ir.sequence', 'write', [purchase_journal['sequence_id'][0], {
        #         'prefix': config.get(key, {}).get('data', {}).get('supplier_invoice', "")}], {'context': context})
        # if config.get(key, {}).get('data', {}).get('supplier_refund', ""):
        #     self.execute_odoo('ir.sequence', 'write', [purchase_journal['refund_sequence_id'][0], {
        #         'prefix': config.get(key, {}).get('data', {}).get('supplier_refund', "")}], {'context': context})
