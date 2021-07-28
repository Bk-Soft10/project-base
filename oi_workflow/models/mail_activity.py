'''
Created on Apr 18, 2019

@author: Zuhair Hammadi
'''
from odoo import models, api

class MailActivity(models.Model):
    _inherit = 'mail.activity'
    
    def activity_format(self):
        activity_type_approval = self.env.ref('oi_workflow.activity_type_approval')
        self = self.filtered(lambda record : record.activity_type_id != activity_type_approval)
        return super(MailActivity, self).activity_format()