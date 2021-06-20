# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
# -*- coding: utf-8 -*-
##############################################################################
#
##############################################################################
{
    'name': 'Fin App',
    'version': '1.1',
    'author': 'BK Software',
    'category': 'Company Systems',
    'sequence': 2,
    'website': 'https://www.odoo.com',
    'summary': 'Developer IT',
    'description': """
Application Fin App
==========================

This application enables you to manage accounting, sale, purhcase etc...


In This Module:
============================
* Accounting Managament
* Wherehouse Management
* Purchase Management
* Sale Management
    """,
    'depends': [
        'base',
        'web',
        'mail',
        'resource',
        'account',
        'analytic',
        'sale_management',
        'sale',
        'purchase',
        'sale_stock',
        # 'sales_team',
        # 'crm',
        'stock',
        'product',
        # 'product_expiry',
        # 'point_of_sale',
        # 'barcodes',
        'account_pdc',
    ],
    'data': [
        'security/fin_security.xml',
        'security/ir.model.access.csv',
        'views/fin_view.xml',
        'views/res_config_settings_views.xml',
        # 'views/fin_product_view.xml',
        # 'views/fin_sale_view.xml',
        # 'wizard/wiz_fin_order_report_view.xml',
        # 'wizard/wiz_fin_view.xml',
        # 'report/fin_app_report.xml',
        'report/fin_app_order_report.xml',
        'report/app_sale_report.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
