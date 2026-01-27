# -*- coding: utf-8 -*-
{
    'name': 'Web Notifications Lite',
    'version': '19.0.1.0.0',
    'category': 'Tools',
    'summary': 'Web Notifications with Pop-Up and Breaking News Types',
    'description': """
        Web Notification Module for Odoo 19
        ====================================
        This module provides two types of web notifications:
        
        1. Pop-Up Type Notifications - Toast-style notifications on the right side
        2. Breaking News Type Notifications - Scrolling banner at the top
        
        Features:
        - State management (Draft → In Progress → Finish)
        - User permission controls
        - Target specific users or all users
        - Customizable breaking news styling (colors, font size, direction)
        - Expiry date for breaking news
    """,
    'author': 'Zekrom Tech',
    'website': 'https://www.zekromtech.com',
    'license': 'LGPL-3',
    'depends': ['base', 'web'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/web_notification_views.xml',
        'views/res_users_views.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'zk_notification_lite/static/src/css/notification.css',
            'zk_notification_lite/static/src/js/notification_service.js',
            'zk_notification_lite/static/src/js/notification_systray.js',
            'zk_notification_lite/static/src/js/popup_notification.js',
            'zk_notification_lite/static/src/js/breaking_news.js',
            'zk_notification_lite/static/src/xml/notification_templates.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
