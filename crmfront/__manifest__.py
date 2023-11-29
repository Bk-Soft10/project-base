{
    'name': 'Odoo CRM Frontend',

    'summary': """
        An Odoo-CRM Frontend to provide clients an easy to use and Intuitive user interface.""",

    'description': """
        An Odoo-CRM web frontend for clients to interact with the Odoo-CRM platform in a simple to use Interface that gives them funtionality
        to track their service requests to the business.
    """,

    'author': 'Kola Technologies Ltd',
    'website': 'https://kolapro.com',
    'category': 'Productivity',
    'license': 'AGPL-3',
    'version': '0.2',
    #'price': '9.9',
    #'currency': 'EUR',
    'support': 'admin@kolapro.com',

    'depends': ['base','product','contacts', 'auth_signup', 'website', 'crm', 'hr'],
    'live_test_url':'https://crmfront.kolapro.com',
    'data': [
        #--------data files--------#
        "data/crm_data.xml",

        #--------security files--------#
        'security/security.xml',
        'security/ir.model.access.csv',

        #--------backend views--------#
        'views/backend/crm_business_admin_menu.xml',
        'views/backend/res_partner_views.xml',
        'views/backend/res_users_views.xml',
        'views/backend/crm_lead_category.xml',
        'views/backend/crm_leads_views.xml',
        'views/backend/email_templates.xml',
        'views/backend/service_views.xml',
        'views/backend/crm_menu_views.xml',
        
        #--------frontend views--------#
        'views/frontend/crm_dashboard_assets.xml',
        'views/frontend/crm_dashboard_form.xml',
        'views/frontend/comment_views.xml',
        'views/frontend/portal_views.xml',
        'views/frontend/ticket_view.xml',
        'views/frontend/crm_lead_submitted.xml',
        'views/frontend/crm_dashboard_views.xml',
        'views/frontend/auth_signup_views.xml',
    ],
    
    'images':[
        'static/description/banner.png'
    ],

    "assets": {
        "web.assets_backend": [
            "https://fonts.googleapis.com/css?family=Source+Sans+Pro:300,400,400i,700",
            "/crmfront/static/src/css/kanban.css",
            "https://fonts.googleapis.com/css?family=Open+Sans:300,400,600,700",
            "/crmfront/static/src/css/materialdesignicons.min.css",
            "/crmfront/static/src/css/layout.css",
        ],

    },
    
}
