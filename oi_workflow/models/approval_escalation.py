'''
Created on Feb 17, 2019

@author: Zuhair Hammadi
'''
from odoo import models, fields

class ApprovalEscalation(models.Model):
    _name = 'approval.escalation'
    _description = 'Approval Workflow Escalation'
            
    config_id = fields.Many2one('approval.config', required = True, ondelete ='cascade')    
    automation_id = fields.Many2one('base.automation', string='Automated Action', required=True, ondelete='restrict', delegate=True)
    active = fields.Boolean(related='automation_id.active', store = True, readonly = False)
            
    def unlink(self):
        automation_ids = self.mapped('automation_id')
        action_server_ids = self.mapped('action_server_id')
        res = super(ApprovalEscalation, self).unlink()
        automation_ids.unlink()
        action_server_ids.unlink()
        return res