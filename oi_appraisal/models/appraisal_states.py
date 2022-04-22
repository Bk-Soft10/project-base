'''
Created on Feb 3, 2019

@author: Zuhair Hammadi
'''
from odoo import models, fields, api

class AppraisalStatus(models.Model):
    _name = 'appraisal.states'
    _description = 'Appraisal States'
    
    name = fields.Char(requried = True)
    state = fields.Char(requried = True)
    
    @api.model
    def _update_states(self):
        records = self.search([])
        states = self.env['appraisal']._get_state()
        for state, name in states:
            record = self.filtered(lambda record: record.state == state)
            if record:
                if record.name != name:
                    record.name = name
                records -=record
            else:
                record=self.create({'name' : name , 'state' : state})            
        records.unlink()
        
    def init(self):
        self._update_states()