'''
Created on Jul 4, 2020

@author: Zuhair Hammadi
'''
from odoo import models, api

class IrModel(models.Model):
    _inherit = 'ir.model'
    
    @api.model
    def _instanciate(self, model_data):
        model_class = super(IrModel, self)._instanciate(model_data)
        if isinstance(model_class._inherit, list) and 'mail.thread.blacklist' in model_class._inherit and 'mail.thread' in model_class._inherit:
            model_class._inherit.remove('mail.thread')
        
        if model_data.get('is_mail_blacklist') and model_class._custom and not hasattr(model_class,'_primary_email') :
            model_class._primary_email = 'x_email'
        
        return model_class