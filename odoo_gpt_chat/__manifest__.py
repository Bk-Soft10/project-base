{
    'name': 'AI Chatbot',
    'version': '1.0',
    'category': 'Website',
    'sequence': 40,
    'author': 'Terabits Technolab',
    'license': 'OPL-1',
    'description': "AI Chatbot | ChatGPT Live chat Support with your own data | AI chatbot with custom knowledge",
    'summary': "AI-powered search bar and chatbot platform that helps users find answers quickly and easily",
    'depends': ['base', 'base_setup', 'web'],
    'data': ['views/settings_whisper_patch.xml'],
    'installable': True,
    'application': True,
    'website': 'https://www.whisperchat.ai/',
    'images': ['static/description/banner.gif'],
    'live_test_url': 'https://www.whisperchat.ai/demo',
    'assets': {
        'web.assets_frontend': ['/odoo_gpt_chat/static/src/notificationPatch.js'],
        'web.assets_backend': ['/odoo_gpt_chat/static/src/notificationPatch.js']
    }
}
