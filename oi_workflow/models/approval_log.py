'''
Created on Nov 2, 2017

@author: Zuhair Hammadi
'''
from odoo import models, fields, api

class ApprovalLog(models.Model):
    _name = 'approval.log'
    _description = 'Approval Workflow Log'
    _log_access = False
    _order = 'id desc'
    
    model_id = fields.Many2one('ir.model', string='Object', required = True, ondelete='cascade')
    record_id = fields.Integer(required = True)
    user_id = fields.Many2one('res.users', 'User', required = True)
    
    state = fields.Char(required = True)    
    
    name = fields.Char('New Status', compute = '_calc_name')
    old_name = fields.Char(compute = '_calc_old_name', string='Old Status')
        
    date = fields.Datetime('Date', required = True)
    
    description = fields.Text()
    
    @api.depends('state', 'model_id')
    def _calc_name(self):
        for record in self:
            model = self.env[record.model_id.model]
            vals = dict(model._fields['state']._description_selection(self.env))
            record.name = vals.get(record.state, record.state)
    
    @api.depends('name')
    def _calc_old_name(self):
        for record in self:
            record.old_name = self.search([('model_id','=', record.model_id.id), ('record_id','=', record.record_id), ('id','<', record.id)], order = 'id desc', limit = 1)[:1].name