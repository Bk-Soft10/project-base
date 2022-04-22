'''
Created on Nov 13, 2018

@author: Zuhair Hammadi
'''
from odoo import models, fields, _
from odoo.exceptions import UserError

class AppraisalGenerate(models.TransientModel):
    _name = 'appraisal.generate'
    _description = 'Appraisal Generate'
    
    employee_ids = fields.Many2many('hr.employee', string='Employees', required = True)
    
    def generate(self):
        if not self.employee_ids:
            raise UserError(_("You must select employee(s) to generate appraisal(s)."))
        
        batch = self.env['appraisal.batch'].browse(self._context.get('active_id'))
        
        records = self.env['appraisal']
                
        for employee in self.employee_ids:
            records +=batch._generate(employee)
            
        records._calc_parent_id()
            
        
        return batch.action_view_appraisal()
        
            