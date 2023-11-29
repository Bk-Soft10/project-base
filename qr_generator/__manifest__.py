# -*- coding: utf-8 -*-
{
    'name': "QR Code Generator",
    'summary': """Integrated QR code generator within the odoo framework.""",
    'description': """Helps to generate QR codes for texts or large urls.""",
    'version': '15.0.1.0.0',
    'category': 'Tools',
    'author': "Kripal K",
    'website': "https://www.linkedin.com/in/kripal754/",
    'license': 'LGPL-3',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv'
    ],
    'assets': {
        'web.assets_backend': [
            'qr_generator/static/src/js/qr_generator.js',
            'qr_generator/static/src/scss/qr_generator.scss'
        ],
        'web.assets_qweb': [
            'qr_generator/static/src/xml/qr_generator.xml'
        ],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
