# -*- coding: utf-8 -*-
#############################################################################
# app_financial_report
#############################################################################

{
    'name': 'Financial Reports',
    'version': '1.0.0',
    'summary': """Print pdf reports of Financial Reports with Bksoftware""",
    'description': """Print pdf reports of Financial Reports with Bksoftware""",
    'author': "BKsoftware",
    'website': "https://www.bksoftware.com",
    'category': 'Accounting',
    'depends': [
        'account',
        'base_accounting_kit',
        'report_xlsx',
    ],
    'data': [
        'wizard/account_report_view.xml',
        'wizard/wizard_account_report_view.xml',
        'reports/financial_report.xml',
        'reports/account_report_view.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
