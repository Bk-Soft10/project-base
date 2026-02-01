{
    'name': 'Purchase From Sale',
    'version': '1.0',
    'sequence': 69,
    'author': 'BK-Software',
    'license': 'OPL-1',
    'category': 'Master',
    'summary': 'purchase from sale',
    'description': 'purchase from sale',
    'depends': [
        'sale_management',
        'purchase',
    ],
    'data': [
        # 'wizard/sale_rfq_wizard.xml',
        'views/views.xml',
        'views/res_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
