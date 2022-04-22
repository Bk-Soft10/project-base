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
from datetime import datetime, date, time, timedelta
from odoo import models, fields, api, exceptions, _, SUPERUSER_ID


class ProductProduct(models.Model):
    _inherit = 'product.product'

    our_price_deduct = fields.Float('Variant Deduct Price',  help="This is the sum of the our deduct price of all attributes")
    our_price = fields.Float(string="Our Price", compute="_compute_product_our_price")
    total_saving = fields.Float(string="Total Saving", compute="compute_total_saving")

    def _compute_product_our_price_deduct123(self):
        for product in self:
            if product.product_template_attribute_value_ids:
                product.our_price_deduct = sum(product.product_template_attribute_value_ids.mapped('our_price_deduct'))
            else:
                product.our_price_deduct = 0.00

    @api.depends('list_price', 'our_price_deduct')
    @api.depends_context('uom')
    def _compute_product_our_price(self):
        to_uom = None
        if 'uom' in self._context:
            to_uom = self.env['uom.uom'].browse(self._context['uom'])
        for product in self:
            if to_uom:
                list_price = product.uom_id._compute_price(product.list_price, to_uom)
            else:
                list_price = product.list_price
            total_price = list_price + product.price_extra
            if product.our_price_deduct and total_price > product.our_price_deduct:
                product.our_price = total_price - product.our_price_deduct
            else:
                product.our_price = 0.00

    def compute_total_saving(self):
        for record in self:
            if record.lst_price:
                record.total_saving = 0.00
                if record.our_price and record.lst_price > record.our_price:
                    record.total_saving = record.lst_price - record.our_price
            else:
                record.total_saving = 0.00

