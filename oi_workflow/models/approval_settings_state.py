'''
Created on Jul 15, 2019

@author: Zuhair Hammadi
'''
from odoo import models, fields, api

class ApprovalSettingsStatus(models.Model):
    _name = 'approval.settings.state'
    _description = 'Approval Workflow Static Status'
    _order = 'type desc,sequence'

    settings_id = fields.Many2one('approval.settings', required = True, ondelete='cascade', string='Model Settings')
    sequence = fields.Integer(default = 0, required = True, copy = False)
    state = fields.Char(required = True)
    name = fields.Char(required = True, translate = True)
    active = fields.Boolean(default = True)
    type = fields.Selection([('before', 'Before Approval'), ('after', 'After Approval')], required = True)
    reject_state = fields.Boolean()    
    
    _sql_constraints = [
        ('state_uniq', 'unique (settings_id,state)', 'The state should be unique !'),
    ]    
    
    
    @api.onchange('sequence')
    def _onchange_sequence(self):
        if self.settings_id and not self.sequence:
            sequences = self.mapped('settings_id.state_ids.sequence')
            self.sequence = (sequences and max(sequences) or 0) + 1
            
            
    @api.model_create_multi
    @api.returns('self', lambda value:value.id)
    def create(self, vals_list):
        self.clear_caches()
        records = super(ApprovalSettingsStatus, self).create(vals_list)
        for lang in self.env['res.lang'].search([('active','=', True), ('code','!=', 'en_US')]):
            lang = lang.code
            context = dict(self._context, lang=lang)
            env2 = self.env(context = context)
            for record in records:
                trl = env2['ir.translation']._get_source(None, ('code',), lang, record.name)
                if trl != record.name:
                    record.with_context(context).write({'name' : trl})
            
        return records
    
    def write(self, vals):
        self.clear_caches()
        return super(ApprovalSettingsStatus, self).write(vals)
    
    def unlink(self):
        self.clear_caches()
        return super(ApprovalSettingsStatus, self).unlink()