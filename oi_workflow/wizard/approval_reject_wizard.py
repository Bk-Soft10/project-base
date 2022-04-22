'''
Created on Sep 24, 2018

@author: Zuhair Hammadi
'''
from odoo import models, fields, api

class ApprovalRejectWizard(models.TransientModel):
    _name = 'approval.reject.wizard'
    _description = 'Approval Workflow Reject Wizard'
    
    def _get_reject_confirm_msg(self):
        model = self._context.get('active_model')
        record_id = self._context.get('active_id')
        record = self.env[model].browse(record_id)
        assert record._isinstance('approval.record')        
        return record.reject_confirm_msg
        
    
    reason = fields.Text(required = True)
    reject_confirm_msg = fields.Char(default = _get_reject_confirm_msg, readonly = True)
    
    def action_reject(self):
        model = self._context.get('active_model')
        record_id = self._context.get('active_id')
        record = self.env[model].browse(record_id)
        assert record._isinstance('approval.record')
        record.action_reject(self.reason)