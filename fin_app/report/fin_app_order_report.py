#-*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models
import datetime
import logging
#from num2words import num2words
#from openerp.addons.check_followups.models.money_to_text_ar import amount_to_text_arabic
_logger = logging.getLogger(__name__)



class app_freight_import_report(models.AbstractModel):
    _name = 'report.fin_app.fin_app_order_report'

    def _get_domain_pass(self, wiz):
        if wiz and wiz.date_from and wiz.date_to:
            do_lst = [('create_date', '>=', wiz.date_from), ('create_date', '<=', wiz.date_to)]
            if wiz.partner_ids:
                do_lst.append(('partner_id.id', 'in', wiz.partner_ids.ids))
            return do_lst

    def _get_invoice_data(self,wiz):
        domain_lst = self._get_domain_pass(wiz) or []
        if wiz and wiz.state == 'confirm':
            domain_lst.append(('state', 'in', ['open', 'in_payment', 'paid']))
        if wiz and wiz.report_type in ['out_invoice', 'in_invoice', 'out_refund', 'in_refund']:
            domain_lst.append(('type', '=', wiz.report_type))
        return self.env['account.invoice'].search(domain_lst)

    def _get_payment_data(self,wiz):
        domain_lst = self._get_domain_pass(wiz) or []
        if wiz and wiz.state == 'confirm':
            domain_lst.append(('state', 'in', ['posted', 'sent', 'reconciled']))
        if wiz and wiz.report_type in ['inbound', 'outbound']:
            domain_lst.append(('payment_type', '=', wiz.report_type))
        return self.env['account.payment'].search(domain_lst)

    def _get_purchase_data(self,wiz):
        domain_lst = self._get_domain_pass(wiz) or []
        if wiz and wiz.state == 'confirm':
            domain_lst.append(('state', 'in', ['purchase']))
        return self.env['purchase.order'].search(domain_lst)

    def _get_sale_data(self, wiz):
        domain_lst = self._get_domain_pass(wiz) or []
        if wiz and wiz.state == 'confirm':
            domain_lst.append(('state', 'in', ['sale']))
        return self.env['sale.order'].search(domain_lst)

    @api.model
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        model_id = self.env[model].browse(self.env.context.get('active_id'))
        docargs = {
            'doc_ids': docids,
            'doc_model': model,
            'docs': model_id,
            'data': data,
            'get_invoice_data': self._get_invoice_data,
            'get_payment_data': self._get_payment_data,
            'get_purchase_data': self._get_purchase_data,
            'get_sale_data': self._get_sale_data,
        }
        return docargs
