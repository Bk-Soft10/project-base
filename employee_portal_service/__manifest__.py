# -*- coding: utf-8 -*-
####################################
####################################

{
    'name': 'Employees Portal Services',
    'version': '1.0',
    'sequence': '0',
    'author': 'TBS',
    'summary': 'Website',
    'description': """
     Website
""",
    'depends': [
        'web',
        'website',
        'portal',
        'auth_signup',
        'hr',
        'hr_contract',
        'hr_expense',
        'om_hr_payroll',
    ],
    'data': [
        'security/portal_security.xml',
        'security/ir.model.access.csv',
        'views/menus.xml',
        'views/views.xml',
        'views/res_config_settings_views.xml',
        # 'views/assets.xml',
        'views/templates.xml',
        'views/pages/portal_home.xml',
        'views/pages/profile/profile_employee.xml',
        'views/pages/contract/contract_list.xml',
        'views/pages/contract/contract_view.xml',
        'views/pages/transaction/transaction_list.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
