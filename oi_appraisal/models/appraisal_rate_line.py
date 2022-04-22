'''
Created on Nov 12, 2018

@author: Zuhair Hammadi
'''

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AppraisalRateLine(models.Model):    
    _name = 'appraisal.rate.line'
    _description = 'Appraisal Rate Line'
    _order = 'value'
    
    name = fields.Char(required = True)
    description = fields.Char()
    value = fields.Float()
    rate_type_id = fields.Many2one('appraisal.rate', required = True, ondelete='cascade')
    
    _sql_constraints= [
            ('name_unqiue', 'unique(rate_type_id, name)', 'Name must be unique!')
        ]                
    
    @api.constrains('value')
    def _check_value(self):
        for record in self:
            if record.value < 0:
                raise ValidationError(_('Value must be positive'))
            
    
    def name_get(self):
        res = []
        for record in self:
            value = record.value
            if value == int(value):
                value = int(value)
            res.append((record.id, '[%s] %s' % (value, record.name)))
        return res