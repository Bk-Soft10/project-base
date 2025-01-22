# -*- coding: utf-8 -*-
# Part of LaxiconSolution. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import html2text

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def send_by_whatsapp(self):
        model_id = self.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)
        default_mail_template_id = self.env['mail.template'].search([('model_id', '=', model_id.id)], limit=1)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Send to WhatsApp',
            'res_model': 'send.whatsapp.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_model_id': model_id.id, 'default_res': self.id, 
            'default_mail_template_id': default_mail_template_id.id,'default_mobile_number': self.mobile},
            
        }

    

