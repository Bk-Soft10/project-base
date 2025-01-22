# -*- coding: utf-8 -*-
# Part of LaxiconSolution. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import html2text


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def send_by_whatsapp(self):
        model_id = self.env['ir.model'].search([('model', '=', 'stock.picking')], limit=1)
        default_mail_template_id = self.env.ref('lax_whatsapp_stock.stock_picking_email_template')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Send to WhatsApp',
            'res_model': 'send.whatsapp.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_model_id': model_id.id, 'default_res': self.id, 
            'default_mail_template_id': default_mail_template_id.id,'default_mobile_number': self.partner_id.mobile},
        }
