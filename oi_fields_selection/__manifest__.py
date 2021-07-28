# -*- coding: utf-8 -*-
{
    'name': "Field Selection Configuration",

    'summary': """Change field selection options from Odoo interface, Field Configuration, Database Structure, Custom Module""",

    'description': """
        Change field selection options from odoo interface without need a custom module
    """,

    'author': "Openinside",
    'website': "https://www.open-inside.com",
    "license": "OPL-1",
    "price" : 27,
    "currency": 'EUR',    

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Extra Tools',
    'version': '13.0.1.1.13',

    # any module necessary for this one to work correctly
    'depends': ['base', 'oi_base'],

    # always loaded
    'data': [
        'view/ir_model_fields.xml',
        'view/ir_model_fields_selection.xml',
        'security/ir.model.access.csv'
    ],
    
    'external_dependencies' : {
        
    },
    'odoo-apps' : True,
    'auto_install': True,
    'images':[
        'static/description/cover.png'
    ]     
}