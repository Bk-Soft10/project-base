'''
Created on Jul 14, 2019

@author: Zuhair Hammadi
'''
from odoo import models, fields, api

class ApprovalSettings(models.Model):
    _name = 'approval.settings'
    _description = 'Approval Workflow Model Settings'
    _rec_name = 'model'
    _order = 'model'
        
    model_id = fields.Many2one('ir.model', string='Object', required = True, ondelete='cascade', domain = [('field_id.name','=', 'state'), ('transient','=', False)])
    
    model = fields.Char(related='model_id.model', store = True, readonly = True)
    model_name = fields.Char(related='model_id.name', readonly = True)
    
    state_ids = fields.One2many('approval.settings.state', 'settings_id', context={'active_test' : False})
    
    on_submit = fields.Text()
    on_approve = fields.Text()
    on_approval = fields.Text()
    on_reject = fields.Text()
    on_forward = fields.Text()
    on_return = fields.Text()
    on_transfer = fields.Text()
    
    approval_count = fields.Integer(compute = '_calc_approval_count')    
    
    _sql_constraints = [
        ('model_uniq', 'unique (model_id)', 'The model should be unique !'),
    ]    
    
    
    def _default_states(self):
        model = self.model_id.model
        sequence = 0
        res =[]
        for state, name in self.env[model]._before_approval_states():
            sequence +=1
            res.append({
                'state' : state,
                'name' : name,
                'type' : 'before',
                'sequence' : sequence
                })
        for state, name in self.env[model]._after_approval_states():
            sequence +=1
            res.append({
                'state' : state,
                'name' : name,
                'type' : 'after',
                'sequence' : sequence,
                'reject_state' : state=='rejected'
                })           
        return res     
    
    
    def reset_states(self):
        self.state_ids.unlink()
        for vals in self._default_states():
            vals['settings_id'] = self.id
            self.env['approval.settings.state'].create(vals)          
        
    
    @api.onchange('model_id')
    def _onchange_model_id(self):
        if not self.state_ids and self.model_id:
            for vals in self._default_states():
                self.state_ids += self.env['approval.settings.state'].new(vals)
                
    @api.depends('model_id')
    def _calc_approval_count(self):
        for record in self:
            record.approval_count = self.env['approval.config'].search([('model_id', '=', record.model_id.id)], count = True)
                    
        
    def action_view_approval(self):
        model_id = self.model_id.id
        return  {
            'type' : 'ir.actions.act_window',
            'name' : 'Workflow',
            'res_model' : 'approval.config',
            'view_mode' : 'tree,form',
            'context' : {'default_model_id' : model_id},
            'domain' : [('model_id','=', model_id)]
            }
                    