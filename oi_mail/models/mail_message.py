'''
Created on Jul 14, 2020

@author: Zuhair Hammadi
'''
from odoo import models, api

class Message(models.Model):
    _inherit = 'mail.message'
    
    @api.model_create_multi
    @api.returns('self', lambda value:value.id)
    def create(self, vals_list):
        if self._context.get('default_parent_id'):
            self = self.with_context(default_parent_id = None)            
        return super(Message, self).create(vals_list)