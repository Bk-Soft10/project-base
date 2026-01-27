{
    'name': 'Forced Two-Factor Authentication (2FA)',
    'summary': 'Enforces TOTP two-factor authentication for all users',

    'author': 'Kitworks Systems',
    'website': 'https://github.com/kitworks-systems/addons',

    'category': 'Extra Tools/Security',
    'license': 'LGPL-3',
    'version': '19.0.1.0.0',

    'depends': [
        'auth_totp',
        'web',
    ],

    'external_dependencies': {
        'python': [],
    },

    'data': [
        'views/templates_for_2fa.xml',
    ],
    'demo': [
    ],

    'assets': {
        'kw_2fa.kw_2fa_assets': [
            'kw_2fa/static/src/css/kw_style.css',
        ],
    },

    'installable': True,
    'auto_install': False,
    'application': False,

    'images': [
        'static/description/cover.png',
        'static/description/icon.png',
    ],

}
