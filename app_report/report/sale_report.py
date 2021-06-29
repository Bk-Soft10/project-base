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
        saleperson_data = []
        partner_data = []
        product_data = []
        if docs.status == 'order':
            status = ['sale', 'done']
        else:
            status = ['draft', 'sent', 'sale', 'done']
        if not docs.product_ids and docs.group_by == 'product':
            product_ids = self.env['product.template'].search([('sale_ok', '=', True)]) or False
        if not docs.partner_ids and docs.group_by == 'partner':
            partner_ids = self.env['res.partner'].search([('customer_rank', '>', 0)]) or False
        if not docs.user_ids and docs.group_by == 'user':
            user_ids = self.env['res.users'].search([('groups_id', 'in', self.env.ref('sales_team.group_sale_salesman').id)]) or False
        # domain_order_wiz = [('date_order', '>=', docs.date_from), ('date_order', '<=', docs.date_to), ('state', 'in', status)]
        # domain_order_line_wiz = [('order_id.date_order', '>=', docs.date_from), ('order_id.date_order', '<=', docs.date_to), ('order_id.state', 'in', status)]

        if docs.group_by == 'product' and product_ids:
            product_lst = product_ids.ids or []
            product_lst.append(0)
            self._cr.execute("SELECT templ.name , " \
                       "min(templ.id), " \
                       "sum(ord_line.product_uom_qty), " \
                       "sum(ord_line.qty_delivered), " \
                       "sum(ord_line.qty_invoiced), " \
                       "sum(ord_line.price_unit) " \
                       "FROM sale_order_line ord_line " \
                       "INNER JOIN sale_order_line so " \
                       "on so.id = ord_line.order_id " \
                       "INNER JOIN product_product prod " \
                       "on prod.id = ord_line.product_id " \
                       "INNER JOIN product_template  templ " \
                       "on templ.id = prod.product_tmpl_id " \
                       "where templ.active = TRUE AND so.state in " + str(tuple(status)) + " AND so.create_date BETWEEN '" + str(docs.date_from) + "' AND '" + str(docs.date_to) + "' AND templ.id in " + str(tuple(product_lst or [])) + " GROUP BY templ.name " \
                          "ORDER BY templ.name ASC")
            for pro_line in self._cr.fetchall():
                product_data.append({
                    'product_name': pro_line[0],
                    'qty_order': pro_line[2],
                    'qty_delivered': pro_line[3],
                    'qty_invoiced': pro_line[4],
                    'price_unit': pro_line[5],
                })
        if docs.group_by == 'partner' and partner_ids:
            partner_lst = partner_ids.ids or []
            partner_lst.append(0)
            self._cr.execute("SELECT partner.name , " \
                       "min(partner.id), " \
                       "count(so.id), " \
                       "sum(so.amount_total) " \
                       "FROM sale_order so " \
                       "INNER JOIN res_partner partner " \
                       "on partner.id = so.partner_id " \
                       "where so.state in " + str(tuple(status)) + " AND so.create_date BETWEEN '" + str(docs.date_from) + "' AND '" + str(docs.date_to) + "' AND partner.id in " + str(tuple(partner_lst or [])) + " GROUP BY partner.name " \
                        "ORDER BY partner.name ASC")
            for partner_line in self._cr.fetchall():
                partner_data.append({
                    'partner': partner_line[0],
                    'no_ordered': partner_line[2],
                    'amount_total': partner_line[3],
                })
        if docs.group_by == 'user' and user_ids:
            user_lst = user_ids.ids or []
            user_lst.append(0)
            # self._cr.execute("SELECT userr.name_partner , " \
            #            "min(user.id), " \
            #            "count(so.id), " \
            #            "sum(so.amount_total) " \
            #            "FROM sale_order so " \
            #            "INNER JOIN res_users userr " \
            #            "on userr.id = so.user_id " \
            #            "where so.state in " + str(tuple(status)) + " AND so.create_date BETWEEN '" + str(docs.date_from) + "' AND '" + str(docs.date_to) + "' AND user.id in " + str(tuple(user_lst or [])) + " GROUP BY userr.name_partner " \
            #             "ORDER BY userr.name_partner ASC")
            self._cr.execute("SELECT partner.name , " \
                       "min(partner.id), " \
                       "count(so.id), " \
                       "sum(so.amount_total) " \
                       "FROM sale_order so " \
                       "INNER JOIN res_users userr " \
                       "on userr.id = so.user_id " \
                       "INNER JOIN res_partner partner " \
                       "on partner.id = userr.partner_id " \
                       "where so.state in " + str(tuple(status)) + " AND so.create_date BETWEEN '" + str(docs.date_from) + "' AND '" + str(docs.date_to) + "' AND userr.id in " + str(tuple(user_lst or [])) + " GROUP BY partner.name " \
                        "ORDER BY partner.name ASC")
            for user_line in self._cr.fetchall():
                saleperson_data.append({
                    'user': user_line[0],
                    'no_ordered': user_line[2],
                    'amount_total': user_line[3],
                })

        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data,
            'docs': docs,
            'product_ids': product_ids,
            'partner_ids': partner_ids,
            'user_ids': user_ids,
            'status': status,
            'product_data': product_data,
            'partner_data': partner_data,
            'saleperson_data': saleperson_data,
        }