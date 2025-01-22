{
    'name': 'Partner Ledger',
    'version': '17.0',
    'category': 'Accounting/Accounting',
    'summary': 'Odoo application will helps to show partner Ledger accounting entries on customer screen.',
    'author': 'INKERP',
    'website': 'https://www.inkerp.com/',
    'depends': ['account'],
    'data': [
        'views/res_partner_view.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': "OPL-1",
    'installable': True,
    'application': True,
    'auto_install': False,
}
