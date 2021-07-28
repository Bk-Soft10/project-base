'''
Created on May 10, 2021

@author: Zuhair Hammadi
'''
from odoo import models, fields

class AppraisalBatchType(models.Model):    
    _name = 'appraisal.batch.type'
    _description = 'Appraisal Batch Type'
    _order = 'sequence,id'
    
    name = fields.Char(required = True, translate = True)
    code = fields.Char()
    sequence = fields.Integer()
    active = fields.Boolean(default = True)    
    
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Name must be unique!'),
    ]    