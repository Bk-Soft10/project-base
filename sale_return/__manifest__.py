# -*- coding: utf-8 -*-
{
    'name': "Sale Return",

    'summary': """
        This Module to manage customer refund """,

    'description': """
        This Module to manage customer refund in Accounting and Warehouse
    """,

    'author': "Abubakar Mamoun",
    'website': "https://www.facebook.com/bksoftware1/",

    'category': 'sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale_management', 'account', 'stock'],

    'data': [
        # security
        'security/ir.model.access.csv',
        # data
            "data/sequence_data.xml",
        # wizard
            "wizard/sale_return_wizard_views.xml",
        # views
            "views/sale_order_return_views.xml",

    ],

    'demo': [

    ],
}