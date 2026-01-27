# -*- coding: utf-8 -*-

{
    # Module Info
    'name': 'Attachemnet Size Limitation',
    'version': '19.0.1.0.0',
    "license": "LGPL-3",
    'summary': "Limit the size attachemnet",
    'description': """
           Module Add the limit of attachemnt size
        """,

    # Author
    "website": "https://pysquad.com/",
    "author": "PySquad Informatics",

    # Dependencies
    'depends': ['base', 'web'],

    # Data
    'data': [
        'views/res_config_settings_view.xml',
        'views/res_users_view.xml',
    ],

    "assets": {
        "web.assets_backend": [
            "pys_attachment_size_limitation/static/src/js/file_uploader.js"
        ]
    },

    'images': [
        'static/description/banner_img.png'
    ],

    # Technical Speci.
    'application': True,
    'installable': True,
    'auto_install': False,

    # Other Info
    'price': 0,
    'currency': 'EUR',
}
