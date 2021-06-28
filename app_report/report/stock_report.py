# -*- coding: utf-8 -*-

import time
from odoo import api, models, _
from odoo.exceptions import UserError


class StockReport(models.AbstractModel):
    _name = 'report.app_report.view_stock_report'

    def _get_opening_balance_in(self, wiz_id, product_id, loc_ids=[], status=[]):
        op_balance = 0.00
        if wiz_id and wiz_id.opening_balance:
            stock_moves = self.env['stock.move'].search([('date', '<', wiz_id.date_from), ('state', 'in', status), ('product_id.product_tmpl_id.id', '=', product_id.id if product_id else False), ('location_dest_id.id', 'in', loc_ids)])
            if wiz_id.status != 'done':
                op_balance = sum(s_line.product_uom_qty for s_line in stock_moves) or False
            else:
                op_balance = sum(s_line.quantity_done for s_line in stock_moves) or False
        else:
            op_balance = 0.00
        return op_balance

    def _get_opening_balance_out(self, wiz_id, product_id, loc_ids=[], status=[]):
        op_balance = 0.00
        if wiz_id and wiz_id.opening_balance:
            stock_moves = self.env['stock.move'].search([('date', '<', wiz_id.date_from), ('state', 'in', status), ('product_id.product_tmpl_id.id', '=', product_id.id if product_id else False), ('location_id.id', 'in', loc_ids)])
            if wiz_id.status != 'done':
                op_balance = sum(s_line.product_uom_qty for s_line in stock_moves) or False
            else:
                op_balance = sum(s_line.quantity_done for s_line in stock_moves) or False
        else:
            op_balance = 0.00
        return op_balance

    def _get_balance_in(self, wiz_id, product_id, loc_ids=[], status=[]):
        qty = 0.00
        if wiz_id:
            stock_moves = self.env['stock.move'].search([('date', '>=', wiz_id.date_from), ('date', '<=', wiz_id.date_to), ('state', 'in', status), ('product_id.product_tmpl_id.id', '=', product_id.id if product_id else False), ('location_dest_id.id', 'in', loc_ids)])
            if wiz_id.status != 'done':
                qty = sum(s_line.product_uom_qty for s_line in stock_moves) or False
            else:
                qty = sum(s_line.quantity_done for s_line in stock_moves) or False
        else:
            qty = 0.00
        return qty

    def _get_balance_out(self, wiz_id, product_id, loc_ids=[], status=[]):
        qty = 0.00
        if wiz_id:
            stock_moves = self.env['stock.move'].search([('date', '>=', wiz_id.date_from), ('date', '<=', wiz_id.date_to), ('state', 'in', status), ('product_id.product_tmpl_id.id', '=', product_id.id if product_id else False), ('location_id.id', 'in', loc_ids)])
            if wiz_id.status != 'done':
                qty = sum(s_line.product_uom_qty for s_line in stock_moves) or False
            else:
                qty = sum(s_line.quantity_done for s_line in stock_moves) or False
        else:
            qty = 0.00
        return qty

    @api.model
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].sudo().browse(self.env.context.get('active_id'))
        product_ids = docs.product_ids or False
        location_lst = docs.location_ids.ids or []
        status = []
        #quantity_done
        if docs.status == 'done':
            status = ['done']
        else:
            status = ['draft', 'waiting', 'confirmed', 'partially_available', 'assigned', 'done']
        if not docs.product_ids:
            product_ids = self.env['product.template'].search([('type', '=', 'product')]) or False
        if not docs.location_ids:
            location_lst = self.env['stock.location'].search([('usage', '=', 'internal')]).ids or []
        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data,
            'docs': docs,
            'status': status,
            'product_ids': product_ids,
            'location_lst': location_lst,
            'get_opening_balance_in': self._get_opening_balance_in,
            'get_opening_balance_out': self._get_opening_balance_out,
            'get_balance_in': self._get_balance_in,
            'get_balance_out': self._get_balance_out,
        }