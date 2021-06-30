# -*- coding: utf-8 -*-

import time
from odoo import api, models, _
from odoo.exceptions import UserError


class PurchaseReport(models.AbstractModel):
    _name = 'report.app_report.view_po_report'

    def _get_data_partner(self, wiz_id, partner_id, status=[]):
        res = {}
        domain_order_wiz = [('date_order', '>=', wiz_id.date_from), ('date_order', '<=', wiz_id.date_to),
                            ('state', 'in', status)]
        if wiz_id and wiz_id.group_by == 'partner':
            if wiz_id.team_id:
                domain_order_wiz.append(('team_id.id', '=', wiz_id.team_id.id or 0))
            domain_order_wiz.append(('partner_id.id', '=', partner_id.id or 0))
            purchase_data = self.env['purchase.order'].search(domain_order_wiz)
            # tot = sum(s_id.product_qty for s_id in purchase_data) or False
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
            purchase_line_data = self.env['purchase.order.line'].search(domain_order_wiz)
            # tot = sum(s_id.product_qty for s_id in purchase_line_data) or False
        else:
            pass
        return res

    @api.model
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].sudo().browse(self.env.context.get('active_id'))
        product_ids = docs.product_ids or False
        partner_ids = docs.partner_ids or []
        status = []
        partner_data = []
        product_data = []
        if docs.status == 'order':
            status = ['purchase', 'done']
        else:
            status = ['draft', 'sent', 'to approve', 'purchase', 'done']
        if not docs.product_ids and docs.group_by == 'product':
            product_ids = self.env['product.template'].search([('purchase_ok', '=', True)]) or False
        if not docs.partner_ids and docs.group_by == 'partner':
            partner_ids = self.env['res.partner'].search([('supplier_rank', '>', 0)]) or False

        if docs.group_by == 'product' and product_ids:
            product_lst = product_ids.ids or []
            product_lst.append(0)
            self._cr.execute("SELECT templ.name , " \
                       "min(templ.id), " \
                       "sum(ord_line.product_qty), " \
                       "sum(ord_line.qty_received), " \
                       "sum(ord_line.qty_invoiced), " \
                       "sum(ord_line.price_unit) " \
                       "FROM purchase_order_line ord_line " \
                       "INNER JOIN purchase_order po " \
                       "on po.id = ord_line.order_id " \
                       "INNER JOIN product_product prod " \
                       "on prod.id = ord_line.product_id " \
                       "INNER JOIN product_template  templ " \
                       "on templ.id = prod.product_tmpl_id " \
                       "where templ.active = TRUE AND po.state in " + str(tuple(status)) + " AND po.date_order BETWEEN '" + str(docs.date_from) + "' AND '" + str(docs.date_to) + "' AND templ.id in " + str(tuple(product_lst or [])) + " GROUP BY templ.name " \
                          "ORDER BY templ.name ASC")
            for pro_line in self._cr.fetchall():
                product_data.append({
                    'product_name': pro_line[0],
                    'qty_order': pro_line[2],
                    'qty_received': pro_line[3],
                    'qty_invoiced': pro_line[4],
                    'price_unit': pro_line[5],
                })
        if docs.group_by == 'partner' and partner_ids:
            partner_lst = partner_ids.ids or []
            partner_lst.append(0)
            self._cr.execute("SELECT partner.name , " \
                       "min(partner.id), " \
                       "count(po.id), " \
                       "sum(po.amount_total), " \
                       "sum(po.paid_total) " \
                       "FROM purchase_order po " \
                       "INNER JOIN res_partner partner " \
                       "on partner.id = po.partner_id " \
                       "where po.state in " + str(tuple(status)) + " AND po.date_order BETWEEN '" + str(docs.date_from) + "' AND '" + str(docs.date_to) + "' AND partner.id in " + str(tuple(partner_lst or [])) + " GROUP BY partner.name " \
                        "ORDER BY partner.name ASC")
            for partner_line in self._cr.fetchall():
                vendor_id = self.env['res.partner'].browse([int(partner_line[1] or 0)])
                partner_data.append({
                    'partner': partner_line[0],
                    'no_ordered': partner_line[2],
                    'amount_total': partner_line[3],
                    'paid_total': partner_line[4],
                    'partner_balance': vendor_id.debit - vendor_id.credit if vendor_id else 0,
                })

        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data,
            'docs': docs,
            'product_ids': product_ids,
            'partner_ids': partner_ids,
            'status': status,
            'product_data': product_data,
            'partner_data': partner_data,
        }