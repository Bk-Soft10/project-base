# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Workshop App',
    'version': '1.0',
    'category': 'Master',
    'author':'BK Software',
    'sequence': 5,
    'summary': 'Workshop App Addons',
    'description': "",
    'website': 'http://www.bksoft.com',
    'depends': [
        'base',
        'base_setup',
        'mail',
        'web',
        'resource',
        'account',
        'fleet',
        'stock',
        'product',
        'uom',
        'analytic',
        'hr',
    ],
    'data': [
        'security/app_workshop_security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/app_workshop_data.xml',
        'views/app_workshop_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
