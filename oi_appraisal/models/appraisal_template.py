'''
Created on Nov 12, 2018

@author: Zuhair Hammadi
'''
from odoo import models, fields, api

class AppraisalTemplate(models.Model):    
    _name = 'appraisal.template'
    _description = 'Appraisal Template'
    _order = 'sequence,id'
    
    name = fields.Char(required=True, translate = True)
    sequence = fields.Integer()
    code = fields.Char()
    active= fields.Boolean(default=True)
    sections_ids = fields.Many2many('appraisal.section')    
    job_ids = fields.One2many('hr.job', 'appraisal_template_id', string='Job Positions')
    
    weight_ids = fields.One2many('appraisal.section.weight', 'template_id', string='Section Weight')
    
    rate_type_id = fields.Many2one('appraisal.rate', 'Result Title Rating', default = lambda self: self.env.ref('oi_appraisal.rate_standard', False))
    
    domain = fields.Char()

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Name must be unique!'),
    ]
            
    
    @api.returns(None, lambda value:value[0])
    def copy_data(self, default=None):
        default = default or {}
        default['name'] = '%s Copy' % self.name
        return super(AppraisalTemplate, self).copy_data(default)