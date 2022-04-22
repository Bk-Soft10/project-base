# -*- coding: utf-8 -*-
# Copyright 2018 Openinside co. W.L.L.
{
    "name": "Workflow Engine Base",
    "summary": "Configurable Workflow Engine, Workflow, Workflow Engine, Approval, Approval Engine, Appraoval Process, Escalation, Multi Level Approval",
    "version": "13.0.1.2.33",
    'category': 'Extra Tools',
    "website": "https://www.open-inside.com",
    "description": """
        Configurable Workflow Engine
         
    """,
    'images':[
        'static/description/cover.png'
    ],
    "author": "Openinside",
    "license": "OPL-1",
    "price" : 400,
    "currency": 'EUR',
    
    "installable": True,
    "depends": [
        'mail', 'oi_base', 'oi_mail', 'web', 'base_automation', 'oi_action_trigger_reload', 'oi_fields_selection'
    ],
    "data": [
        'security/ir.model.access.csv',
        'view/approval_config.xml',
        'view/approval_approve_wizard.xml',
        'view/approval_reject_wizard.xml',
        'view/approval_forward_wizard.xml',
        'view/approval_return_wizard.xml',
        'view/approval_transfer_wizard.xml',
        'view/approval_escalation.xml',
        'view/approval_state_update.xml',
        'view/approval_settings.xml',
        'view/action.xml',
        'view/menu.xml',
        'view/templates.xml',
        'view/web_assets.xml',
        'data/mail_activity_type.xml',
        'data/mail_template.xml',
        'view/res_config_settings.xml',
        'data/ir_cron.xml'
    ],
    'qweb' : [
            "static/src/xml/*.xml",
        ],
    'odoo-apps' : True                   
}

