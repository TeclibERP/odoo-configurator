# -*- coding: utf-8 -*-
# Copyright (C) 2023 - Teclib'ERP (<https://www.teclib-erp.com>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from . import base


class OdooTranslations(base.OdooModule):
    _name = "Translations"
    _key = "translations"

    def apply(self):
        super(OdooTranslations, self).apply()
        self._context['active_test'] = False
        translations = self._datas.get(self._key, {})
        installed_translations = []
        odoo_lang = self.execute_odoo('res.lang', 'search_read', [[('code', 'in', translations)], ['id', 'code', 'active']],
                                      {'context': self._context})
        for lang_code in translations:
            for lang in odoo_lang:
                if lang['code'] == lang_code:
                    if lang['active']:
                        self.logger.info("\t- Translation %s already installed" % lang_code)
                    else:
                        self.logger.info("\t- Install %s Translation" % lang_code)
                        if self._connection._version >= 16:
                            wizard_id = self.execute_odoo('base.language.install', 'create',
                                                          [{'lang_ids': [lang['id']]}])
                        else:
                            wizard_id = self.execute_odoo('base.language.install', 'create', [{'lang': lang_code}])
                        self.execute_odoo('base.language.install', 'lang_install', [wizard_id])
                    installed_translations.append(lang_code)
        missing_translations = set(translations) - set(installed_translations)
        if missing_translations:
            raise Exception("Translations not found : %s" % ", ".join(missing_translations))
