# -*- coding: utf-8 -*-

import time
from odoo import api, models, _
from odoo.exceptions import UserError


class SaleReport(models.AbstractModel):
    _name = 'report.app_report.view_so_report'

    def _get_data_partner(self, wiz_id, partner_id, status=[]):
        res = {}
        domain_order_wiz = [('date_order', '>=', wiz_id.date_from), ('date_order', '<=', wiz_id.date_to),
                            ('state', 'in', status)]
        if wiz_id and wiz_id.group_by == 'partner':
            if wiz_id.team_id:
                domain_order_wiz.append(('team_id.id', '=', wiz_id.team_id.id or 0))
            domain_order_wiz.append(('partner_id.id', '=', partner_id.id or 0))
            sale_data = self.env['sale.order'].search(domain_order_wiz)
            # tot = sum(s_id.product_uom_qty for s_id in sale_data) or False
        else:
            pass
        return res

    def _get_data_saleparson(self, wiz_id, user_id, status=[]):
        res = {}
        domain_order_wiz = [('date_order', '>=', wiz_id.date_from), ('date_order', '<=', wiz_id.date_to),
                            ('state', 'in', status)]
        if wiz_id and wiz_id.group_by == 'user':
            if wiz_id.team_id:
                domain_order_wiz.append(('team_id.id', '=', wiz_id.team_id.id or 0))
            domain_order_wiz.append(('user_id.id', '=', user_id.id or 0))
            sale_data = self.env['sale.order'].search(domain_order_wiz)
            # tot = sum(s_id.product_uom_qty for s_id in sale_data) or False
        else:
            pass
        return res

    def _get_data_product(self, wiz_id, product_id, status=[]):
        res = {}
        domain_order_wiz = [('order_id.date_order', '>=', wiz_id.date_from), ('order_id.date_order', '<=', wiz_id.date_to),
                            ('order_id.state', 'in', status)]
        if wiz_id and wiz_id.group_by == 'user':
            if wiz_id.team_id:
                domain_order_wiz.append(('order_id.team_id.id', '=', wiz_id.team_id.id or 0))
            domain_order_wiz.append(('product_id.product_tmpl_id.id', '=', product_id.id or 0))
            sale_line_data = self.env['sale.order.line'].search(domain_order_wiz)
            # tot = sum(s_id.product_uom_qty for s_id in sale_data) or False
        else:
            pass
        return res

    @api.model
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].sudo().browse(self.env.context.get('active_id'))
        product_ids = docs.product_ids or False
        partner_ids = docs.partner_ids or []
        user_ids = docs.user_ids or False
        status = []
        order_data = []
        product_data = []
        if docs.status == 'done':
            status = ['sale', 'done']
        else:
            status = ['draft', 'sent', 'sale', 'done']
        if not docs.product_ids and docs.group_by == 'product':
            product_ids = self.env['product.template'].search([('sale_ok', '=', True)]) or False
        if not docs.partner_ids and docs.group_by == 'partner':
            partner_ids = self.env['res.partner'].search([('sale_ok', '=', True)]) or False
        if not docs.user_ids and docs.group_by == 'user':
            user_ids = self.env['res.users'].search([('groups_id', 'in', self.env.ref('sales_team.group_sale_salesman').id)]) or False
        domain_order_wiz = [('date_order', '>=', docs.date_from), ('date_order', '<=', docs.date_to), ('state', 'in', status)]
        domain_order_line_wiz = [('order_id.date_order', '>=', docs.date_from), ('order_id.date_order', '<=', docs.date_to), ('order_id.state', 'in', status)]
        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data,
            'docs': docs,
            'product_ids': product_ids,
            'partner_ids': partner_ids,
            'user_ids': user_ids,
            'status': status,
        }