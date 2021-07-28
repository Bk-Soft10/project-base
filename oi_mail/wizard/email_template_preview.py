'''
Created on Oct 2, 2018

@author: Zuhair Hammadi
'''
from odoo import models, api

class TemplatePreview(models.TransientModel):
    _inherit = "email_template.preview"

    @api.onchange('res_id')
    def on_change_res_id(self):
        res = super(TemplatePreview, self).on_change_res_id()
        if self.res_id and self._context.get('template_id'):
            template = self.env['mail.template'].browse(self._context['template_id'])
            if template.needaction_partner_ids:
                mail_values = template.generate_email(self.res_id, ['needaction_partner_ids'])
                self['needaction_partner_ids'] = mail_values.get('needaction_partner_ids', False)
        return res