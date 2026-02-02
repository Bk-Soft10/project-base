{
    "name": 'Auto Barcode Generator',
    "description": """
        Barcode Generator
    """,
    "summary": """
        Barcode Generator on Inventory
    """,
    "category": 'Barcode',
    "author": "One Stop Odoo",
    "website": "https://onestopodoo.com",
    "maintainer": 'One Stop Odoo',
    "version": '1.5',
    "license": 'LGPL-3',
    # Dependencies
    'depends': ['stock'],
    # Views
    'data': [
        'views/product_category_ext.xml',
        'views/product_template_ext.xml',
    ],

   "images": 
    [
        'static/description/banner.gif',
        'static/description/icon.png',
    ],
    "installable": True,
    "auto_install": False,
    'application': True,
}
