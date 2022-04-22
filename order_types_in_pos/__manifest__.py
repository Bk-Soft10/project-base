# -*- coding: utf-8 -*-

{
    'name': "Order Types in POS",
    'version': '13.0.1.0.0',
    'summary': """Specifiy the Order type in POS""",
    'description': """Specifiy the Order type in POS.""",
    'author': "HAK Solutions",
    'company': 'HAK Solutions',
    'category': 'Point of Sale',
    'depends': ['pos_restaurant', 'point_of_sale'],
    'website': 'http://www.HAK Solutions.com',
    'data': [
        'views/views.xml',
        'views/templates.xml',
        'security/ir.model.access.csv'
    ],
    'qweb': ['static/src/xml/*.xml'],
    'images': ['static/description/banner.png'],
     'license': 'OPL-1',
    'price': 0.00,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
    'application': False,
}
