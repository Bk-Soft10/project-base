# -*- coding: utf-8 -*-
# Part of LaxiconSolution. See LICENSE file for full copyright and licensing details.
{
    'name': 'Laxicon Whatsapp Base',
    "author": "Laxicon Solution",
    'license': 'LGPL-3',
    "website": "https://www.laxicon.in",
    "support": "info@laxicon.in",
    "category": "",
    "summary": "Whatsapp Integration",
    "description": """This module is used for whatsapp integration and send message to the customer.""",
    'version': '17.1.0',
    'sequence': 1,
    'depends': ['base', 'mail','contacts'],
    'data': [
        'data/mail_template.xml',
        'security/ir.model.access.csv',
        'wizard/send_whatsapp_msg_wizard_view.xml',
        'views/res_company_view.xml',
        'views/res_partner_view.xml',
        'views/res_config.xml',
    ],
    "images":['static/description/banner.png'],
    'installable': True,
    'application': True,
    'pre_init_hook':  'pre_init_check',
}
