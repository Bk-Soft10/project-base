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
        'views/pages/profile/profile.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
