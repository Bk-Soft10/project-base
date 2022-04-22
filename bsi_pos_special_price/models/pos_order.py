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

class PosOrder(models.Model):
    _inherit = 'pos.order'

    total_saving = fields.Float(string="Total Savings", compute="_compute_total_order_saving")

    @api.depends('lines')
    def _compute_total_order_saving(self):
        for record in self:
            if record.lines:
                temp_total_saving = 0.00
                for line in record.lines:
                    if line.product_id and line.unit_saving and line.unit_saving > 0.00:
                        temp_total_saving += line.unit_saving * line.qty
                record.total_saving = temp_total_saving
            else:
                record.total_saving = 0.00


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    our_price = fields.Float(string="Our Unit Price", compute="_compute_line_our_price_and_unit_saving")
    unit_saving = fields.Float(string="Unit Saving", compute="_compute_line_our_price_and_unit_saving")

    @api.depends('product_id')
    def _compute_line_our_price_and_unit_saving(self):
        for record in self:
            if record.product_id:
                if record.product_id.our_price and record.product_id.total_saving:
                    record.our_price = record.product_id.our_price
                    record.unit_saving = record.product_id.total_saving
                else:
                    record.our_price = 0.00
                    record.unit_saving = 0.00
            else:
                record.our_price = 0.00
                record.unit_saving = 0.00

    @api.depends('qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            if line.our_price > 0.00:
                price = line.our_price * (1 - (line.discount or 0.0) / 100.0)
            else:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

