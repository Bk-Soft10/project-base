# -*- coding: utf-8 -*-
{
    'name': "Website FAQ",
    'summary': """
        Answer the FAQs, and help your Website Users""",

    'description': """By using this application you can answer those questions, that you think these can be the most 
    probably asked questions by your website users or visitors. This will increase the better experience of your 
    website users and visitors.""",
    'author': 'ErpMstar Solutions',
    "license": "LGPL-3",
    'category': 'Website',
    'version': '1.0',
    'depends': ['website'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    'assets': {
        'web.assets_frontend': ['/website_faqs/static/src/js/active_class.js',
                                '/website_faqs/static/src/xml/*.xml']
    },
    # 'qweb': ['static/src/xml/*.xml'],
    'images': [
        'static/description/faq.jpg',
    ],
    'installable': True,
    'website': '',
    'auto_install': False,
    'price': 35,
    'currency': 'EUR',
}
