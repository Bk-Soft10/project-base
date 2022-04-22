from odoo import models, fields, api

class ApprovalRejectWizard(models.TransientModel):
    _name = 'approval.approve.wizard'
    _description = 'Approval Workflow Approve Wizard'
    
    def _get_approve_confirm_msg(self):        
        model = self._context.get('active_model')
        if not model:
            return
        record_id = self._context.get('active_id')
        record = self.env[model].browse(record_id)
        assert record._isinstance('approval.record')        
        return record.approve_confirm_msg                
    
    reason = fields.Text(required = False)
    approve_confirm_msg = fields.Char(default = _get_approve_confirm_msg, readonly = True)

    def action_approve(self):
        model = self._context.get('active_model')
        record_id = self._context.get('active_id')
        record = self.env[model].browse(record_id)
        assert record._isinstance('approval.record')
        record.with_context(reject_reason = self.reason).action_approve()
        
        