# -*- coding: utf-8 -*-
# Part of LaxiconSolution. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _
import html2text
from odoo.exceptions import UserError


class SendWhatsappWizard(models.TransientModel):
    _name = 'send.whatsapp.wizard'
    _description = 'Send Whatsapp Wizard'

    model_id = fields.Many2one('ir.model', string='Model')
    mail_template_id = fields.Many2one('mail.template',string='Mail Template')
    message = fields.Text(string='Message')
    res = fields.Integer(string="Record")
    mobile_number = fields.Char(string="Receipents")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    @api.depends('model_id')
    def onchange_model_id(self):
        if self.model_id:
            self.mail_template_id = self.env['mail.template'].search([('model_id', '=', 'model_id')], limit=1).id

    @api.onchange('mail_template_id', 'res')
    def onchange_mail_template_id_res(self):
        if self.mail_template_id and self.res:

            vals = {
                'mail_template_id': self.mail_template_id.id,
                'resource_ref': '%s,%s' % (self.mail_template_id.model, self.res),
                }

            preview = self.env['mail.template.preview'].create(vals)
            if preview and preview.body_html:
               
                self.message = html2text.html2text(preview.body_html)

            else:
                self.message = 'No content available for preview.'


    def send_to_whatsapp(self):
        active_ids = self._context.get('active_ids', [self.res])
        records = self.env[self.model_id.model].browse(active_ids)
        
        for rec in records:
            filename = f"{rec.name}.pdf"

            # Prepare the message content
            template_id = self.mail_template_id
            vals = {
                'mail_template_id': template_id.id,
                'resource_ref': f'{template_id.model},{rec.id}',
            }
            wiz_id = self.env['mail.template.preview'].create(vals)
            text_message = html2text.html2text(wiz_id.body_html)
            
            if self.mobile_number:
                print("====================================")
                whatsapp_number = self.mobile_number.split(',')
                for num in whatsapp_number:
                    rec.company_id.send_to_whatsapp(
                        whatsapp_number=num, 
                        text_message=text_message,
                        filename=filename or None,
                        media_url=self._context.get('media_url')
                    )
            else:
                raise UserError(_("No Mobile Number Found!"))
