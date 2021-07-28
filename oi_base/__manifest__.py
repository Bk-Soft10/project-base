# -*- coding: utf-8 -*-
# Copyright 2018 Openinside co. W.L.L.
{
    "name": "Base Extension",
    "summary": "Utilities functions for base model",
    "version": "13.0.1.1.29",
    'category': 'Extra Tools',
    "website": "https://www.open-inside.com",
	"description": """
		Utilities functions for base model 
		 
    """,
	'images':[
        'static/description/cover.png'
	],
    "author": "Openinside",
    "license": "OPL-1",
    "price" : 9.99,
    "currency": 'EUR',
    "installable": True,
    "depends": [
        'base', 'web'
    ],
    "data": [
        'view/ir_module_module.xml',
        'view/ir_rule.xml',
        'view/ir_ui_menu.xml',
        'view/ir_actions_server.xml',        
        'view/action.xml',
        'data/res_currency.xml'
    ],
    'external_dependencies' : {
        'python' : ['unidecode'],
    },    
    'installable': True,
    'auto_install': True,    
    'odoo-apps' : True     
}

