{
    "name": "Odoo Whatsapp Template Live Preview",
    "summary": """Preview WhatsApp message templates directly inside the form view instead of using popups. This feature improves usability by providing an inline, seamless preview experience, helping users verify content faster and send messages more efficiently within Odoo Enterprise.""",
    "description": """Preview WhatsApp message templates directly inside the form view instead of using popups. This feature improves usability by providing an inline, seamless preview experience, helping users verify content faster and send messages more efficiently within Odoo Enterprise.""",
    "version": "1.0",
    'author': 'TechUltra Solutions Private Limited',
    "license": "OPL-1",
    'website': 'www.techultrasolutions.com',
    "depends": ["whatsapp"],
    "data": [
        "views/whatsapp_template_view.xml",
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_whatsapp_template_live_preview/static/src/scss/whatsapp_preview.scss',
            'odoo_whatsapp_template_live_preview/static/src/js/whatsapp_preview_controller.js',
        ],
    },
    "installable": True,
    "application": False,
    "images": ['static/description/tus_banner.gif']
}
