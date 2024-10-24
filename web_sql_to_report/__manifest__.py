# -*- coding: utf-8 -*-
{
    'name': "Web Report",

    'summary': """
        create report with query result
        """,

    'description': """
        Long description of module's purpose
    """,

    'author': "Liong",
    'website': "https://www.linkedin.com/in/nagara-liong-50ab07136/",
    "license": "AGPL-3",
    'images': ['static/description/cover.png'],

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv'
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
