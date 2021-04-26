# -*- coding: utf-8 -*-
{
    'name': 'Web Hijri(Islamic) Datepicker',
    'category': 'Extra tools',
    'version': '1.0',
    'author': 'Synconics Technologies Pvt. Ltd',
    'website': "http://www.synconics.com",
    'description': """This module help you to enable Web Hijri(Islamic) Datepicker in Odoo""",
    'depends': ['web'],
    'data': [
        'views/web_hijri_template.xml',
    ],
    'qweb': [
        "static/src/xml/*.xml",
    ],
    'installable': True,
    'auto_install': False,
    'bootstrap': True,
    'application': True,
}
