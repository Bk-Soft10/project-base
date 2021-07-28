'''
Created on Nov 12, 2018

@author: Zuhair Hammadi
'''
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AppraisalRate(models.Model):    
    _name = 'appraisal.rate'
    _description = 'Appraisal Rate'
    
    name = fields.Char(required = True, copy = False)
    lines_ids = fields.One2many('appraisal.rate.line', 'rate_type_id', copy = True)    
    max_value = fields.Float('Max Value', compute='_get_max', store=True)
    
    @api.depends('lines_ids.value')
    def _get_max(self):
        for record in self:
            values = record.mapped('lines_ids.value')
            record.max_value = values and max(values) or 0

    _sql_constraints= [
            ('name_unqiue', 'unique(name)', 'Name must be unique!')
        ]            
    
    @api.constrains('lines_ids', 'max_value')
    def _check_max(self):
        for record in self:
            if record.lines_ids and record.max_value <=0:
                raise ValidationError(_('Max Value must be > 0'))
            
    
    @api.returns(None, lambda value:value[0])
    def copy_data(self, default=None):
        default = default or {}
        if 'name' not in default:
            default['name'] = self.name + _(' (copy)')
        return super(AppraisalRate, self).copy_data(default)