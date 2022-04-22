'''
Created on Oct 2, 2018

@author: Zuhair Hammadi
'''
from odoo import models, api
from odoo.tools.safe_eval import safe_eval

class MailMail(models.Model):
    _inherit = 'mail.mail'

    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def create(self, vals_list):
        for vals in vals_list:
            if isinstance(vals.get('needaction_partner_ids') or False, str):
                value = safe_eval(vals['needaction_partner_ids'])
                if value and isinstance(value, (list, tuple)):
                    if all(isinstance(item, int) for item in value):
                        value = [(6,0, value)]
                vals['needaction_partner_ids'] = value
                
            if 'needaction_partner_ids' in vals:
                vals['notified_partner_ids'] = vals.pop('needaction_partner_ids') or []
                
        return super(MailMail, self).create(vals_list)
        