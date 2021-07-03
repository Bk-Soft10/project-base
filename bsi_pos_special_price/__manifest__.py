# -*- coding: utf-8 -*-
#################################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2021-today Botspot Infoware Pvt ltd'<www.botspotinfoware.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#################################################################################
{
    'name': "POS Special/Saving Prices",
    'author': 'Botspot Infoware Pvt. Ltd.',
    'category': 'Point Of Sale',
    'summary': """POS product saving prices and original prices""",
    'website': 'http://www.botspotinfoware.com',
    'company': 'Botspot Infoware Pvt. Ltd.',
    'maintainer': 'Botspot Infoware Pvt. Ltd.',
    'description': """POS shows the actual price as well as the saving price so, it will be easy to find discounted price. In other sense it shows the original MRP as well as our price of the company.  """, 
    'version': '13.0.0.1',
    'depends': ['base','point_of_sale'],
    'data': [
             'views/product_view.xml',
             'views/sale_view.xml',
             'views/header.xml',
             'views/pos_order_view.xml',
            ],
    "images":  ['static/description/Banner.gif'],
    "qweb":  ['static/src/xml/pos.xml'],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
