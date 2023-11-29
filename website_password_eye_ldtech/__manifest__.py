{
    "name": "Website Password Eye",
    "version": "17.0.1",
    "category": "Website",
    "author": "Livedigital Technologies Private Limited",
    "summary": "Website Password Eye",
    "license": "LGPL-3",
    'website': "ldtech.in",
    "depends": ["web", "website", "auth_signup"],
    "data": [
        "views/templates.xml",
    ],
    'assets': {
        'web.assets_frontend': [
            'website_password_eye_ldtech/static/src/css/custom.css',
            'website_password_eye_ldtech/static/src/js/custom.js',
        ],
    },
    "installable": True,
    'images': ['static/description/icon.png'],
}
