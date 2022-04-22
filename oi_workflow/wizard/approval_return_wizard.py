'''
Created on Nov 11, 2019

@author: Zuhair Hammadi
'''
from odoo import models, fields, api
import json

class ApprovalReturnWizard(models.TransientModel):
    _name = 'approval.return.wizard'
    _description = 'Approval Return Wizard'
    
    @api.model
    def _get_state(self):
        model = self._context.get('active_model')
        if not model:
            return []
            
        selection = dict(self.env[model]._fields['state']._description_selection(self.env))    
        record = self.env[model].browse(self._context.get('active_id'))
        workflow_states = json.loads(record.workflow_states)
        res = []
        for state in workflow_states:
            if state == record.state:
                break
            res.append((state, selection[state]))
        
        if self._context.get('default_state'):
            res.append((self._context['default_state'], selection[state]))
            
        if self._context.get('fixed_return_state'):
            res.append((self._context['fixed_return_state'], selection[state]))
            
        return res
            
                   
    model = fields.Char(default = lambda self: self._context.get('active_model'), required = True)
    record_id = fields.Integer(default = lambda self: self._context.get('active_id'), required = True, string='Record ID')    
    record_ref = fields.Char('Record', compute = '_calc_record_ref')
    
    reason = fields.Text(required = True)    
    state = fields.Selection(_get_state, required = True, string='Status')

    @api.depends('model', 'record_id')
    def _calc_record_ref(self):
        for wizard in self:
            record = self.env[wizard.model].browse(wizard.record_id).exists()
            wizard.record_ref = record and '%s,%d' % (record._name, record.id)            
        
    def action_return(self):
        ctx = self.env.context.copy()
        ctx.pop('default_state', False)
        ctx.pop('fixed_return_state', False)
        record = self.env[self.model].browse(self.record_id)
        record.with_context(ctx)._action_return(self.state, self.reason)
        return {
            'type' : 'ir.actions.client',
            'tag' : 'trigger_reload'
            }        