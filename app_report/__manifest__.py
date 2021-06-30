# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
# -*- coding: utf-8 -*-
##############################################################################
#
##############################################################################
{
    'name': 'App Reports',
    'version': '1.1',
    'author': 'BK Software',
    'category': 'Report',
    'sequence': 2,
    'website': 'https://www.odoo.com',
    'summary': 'more Production reports',
    'description' :"""This module for more Production reports""",
    'depends': [
        'base',
        'web',
        'account',
        'stock',
        'sale',
        'purchase',
    ],
    'data': [
        'views/views.xml',
        'wizard/wizard_account_report_view.xml',
        'wizard/wizard_stock_report_view.xml',
        'wizard/wizard_sale_report_view.xml',
        'wizard/wizard_purchase_report_view.xml',
        'report/report.xml',
        'report/account_report_view.xml',
        'report/stock_report_view.xml',
        'report/sale_report_view.xml',
        'report/purchase_report_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
