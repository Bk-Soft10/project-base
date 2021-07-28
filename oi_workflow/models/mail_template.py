'''
Created on Oct 2, 2018

@author: Zuhair Hammadi
'''
from odoo import models, api

class MailTemplate(models.Model):
    _inherit = "mail.template"
    
    def generate_email(self, res_ids, fields=None):
        res= super(MailTemplate, self).generate_email(res_ids, fields=fields)
        
        if isinstance(res_ids, int):
            results = [res]
        else:
            results = res
                    
        for vals in results:
            if isinstance(vals, dict) and vals.get('model') == 'approval.record':
                vals['model'] = self._context.get('active_model')
        
        return res
    
    @api.model
    def _render_template(self, template_txt, model, res_ids, post_process=False):                
        if model=='approval.record':
            model = self._context.get('active_model')                               
                   
        return super(MailTemplate, self)._render_template(template_txt, model, res_ids, post_process=post_process)
                