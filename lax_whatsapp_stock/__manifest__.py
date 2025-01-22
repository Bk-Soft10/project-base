# -*- coding: utf-8 -*-
# Part of LaxiconSolution. See LICENSE file for full copyright and licensing details.
{
    'name': 'Laxicon Whatsapp Stock',
    "author": "Laxicon Solution",
    "license": "LGPL-3",
    "website": "https://www.laxicon.in",
    "support": "info@laxicon.in",
    "category": "Inventory",
    "summary": "Send Delivery Slip & Stock Reports on Whatspapp",
    "description": """This module is very useful to send Delivery Slip & Stock Reports by Whatsapp easily.""",
    'version': '17.1.0',
    'sequence': 1,
    'depends': ['base', 'stock','lax_whatsapp_base'],
    'data': [
        'data/stock_mail_template.xml',
        'views/stock_view.xml',
       
    ],
    "images":['static/description/banner.png'],
    'installable': True,
    'application': True,
    'pre_init_hook':  'pre_init_check',
}
