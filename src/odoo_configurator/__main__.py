#!/usr/bin/env python3
# Copyright (C) 2023 - Teclib'ERP (<https://www.teclib-erp.com>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from .configurator import Configurator
import argparse


def main():
    parser = argparse.ArgumentParser(description='Odoo Configurator')
    parser.add_argument('files', metavar='files', type=open, nargs='+', help='Config Files To load')
    parser.add_argument('--update', action='store_true', help='Update Mode')
    parser.add_argument('--install', action='store_true', help='Install Mode')
    parser.add_argument('--debug', action='store_true', help='Debug log')
    parser.add_argument('--debug_xmlrpc', action='store_true', help='Debug log xmlrpc')
    parser.add_argument('--keepass', type=str, help='Keepass password')
    args = parser.parse_args()

    c = Configurator([i.name for i in args.files], install=args.install, update=args.update, debug=args.debug,
                     debug_xmlrpc=args.debug_xmlrpc, keepass=args.keepass)
    c.show()
    log = c.start()


if __name__ == '__main__':
    main()
