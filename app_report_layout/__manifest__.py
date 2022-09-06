# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
# -*- coding: utf-8 -*-
{
    'name': 'App Report Layout',
    'version': '1.1',
    'author': 'TBS',
    'category': 'Report',
    'sequence': 12,
    'website': 'https://www.bksoftware.com',
    'summary': 'Layout Report',
    'description': 'Report Addons',
    'depends': [
        'web',
        'base',
    ],
    'data': [
        'views/template_layout.xml',
        'views/company_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
