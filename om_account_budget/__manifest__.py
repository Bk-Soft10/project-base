# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Odoo 13 Budget Management',
    'author': 'Odoo Mates, Odoo SA',
    'category': 'Accounting',
    'description': """Use budgets to compare actual with expected revenues and costs""",
    'summary': 'Odoo 13 Budget Management',
    'depends': ['account'],
    'license': 'LGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'security/account_budget_security.xml',
        'views/account_analytic_account_views.xml',
        'views/account_budget_views.xml',
        'views/res_config_settings_views.xml',
        'wizard/account_budget_analytic_view.xml',
        'wizard/account_budget_crossovered_report_view.xml',
        'wizard/account_budget_crossovered_summary_report_view.xml',
        'wizard/account_budget_report_view.xml',
        'report/account_budget_report.xml',
        'report/report_analyticaccountbudget.xml',
        'report/report_budget.xml',
        'report/report_crossoveredbudget.xml',
    ],
    "images": ['static/description/banner.gif'],
    'demo': ['data/account_budget_demo.xml'],
}
