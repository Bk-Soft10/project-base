'''
Created on Feb 5, 2019

@author: Zuhair Hammadi
'''
from odoo import models, fields

class AppraisalSectionWeight(models.Model):    
    _name = 'appraisal.section.weight'
    _description = 'Appraisal Section Weight'
    
    section_id = fields.Many2one('appraisal.section', required = True, ondelete = 'cascade')
    template_id = fields.Many2one('appraisal.template', required = True, ondelete = 'cascade')
    weight = fields.Float()
    
    _sql_constraints = [
        ('uk', 'unique(section_id,template_id)', 'Must be unique!'),
    ]
    