'''
Created on Nov 13, 2018

@author: Zuhair Hammadi
'''

from odoo import models, fields, api

class AppraisalQuestion(models.Model):    
    _name = 'appraisal.question'
    _description = 'Appraisal Question'
    _order = 'sequence,id'
    
    section_id = fields.Many2one('appraisal.section','Appraisal Section', required=True, readonly = True, ondelete='cascade')
    name = fields.Char(required=True)
    description = fields.Text()
    weight = fields.Float('Weight', default=1)        
    weight_percent = fields.Float('Weight %', compute = '_calc_weight_percent', store = True)       
    sequence = fields.Integer()
    
    rate_type_id = fields.Many2one('appraisal.rate', 'Rating Type')
    
    job_ids = fields.Many2many('hr.job', string='Job Positions')
    
    _sql_constraints = [
        ('name_uniq', 'unique(section_id, name)', 'Name must be unique!'),
    ]

    @api.depends('weight', 'section_id.question_ids.weight')
    def _calc_weight_percent(self):
        for record in self:
            total = sum(record.mapped('section_id.question_ids.weight'))
            record.weight_percent = total and record.weight * 100 / total