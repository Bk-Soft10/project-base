'''
Created on Feb 19, 2019

@author: Zuhair Hammadi
'''
from odoo import models, fields

class IrModelFields(models.Model):
    _inherit = 'ir.model.fields'
    
    selection_count = fields.Integer(compute = '_calc_selection_count')
    
    def _calc_selection_count(self):
        for record in self:
            record.selection_count = self.env['ir.model.fields.selection.custom'].search([('field_id','=', record.id)], count = True)
    
    def action_selections(self):
        assert self.ttype in ['selection', 'reference']
        if not self.env['ir.model.fields.selection.custom'].search([('field_id','=', self.id)], limit = 1):
            env = self.env            
            trl = dict()
            for lang_id in self.env['res.lang'].search([('active','=', True), ('code', '!=', 'en_US')]):        
                env = env(context = dict(env.context, lang=lang_id.code))                  
                vals = dict(self.env[self.model_id.model]._fields[self.name]._description_selection(env))      
                trl[lang_id.code] = vals               

            records = self.env['ir.model.fields.selection.custom']
            sequence = 0
            if env.context['lang'] != 'en_US':
                env = env(context = dict(env.context, lang='en_US'))            
            for value, name in self.env[self.model_id.model]._fields[self.name]._description_selection(env):
                sequence +=1
                records += self.env['ir.model.fields.selection.custom'].create({
                    'field_id' : self.id,
                    'value': value,
                    'name' : name,
                    'sequence' : sequence
                    })
            for lang, vals in trl.items():
                for record in records:
                    value = vals.get(record.value)
                    if value:
                        record.with_context(lang = lang).write({'name' : vals[record.value]})
                
                                                 
        return {
            'type' : 'ir.actions.act_window',
            'name': 'Selections',
            'res_model' : 'ir.model.fields.selection.custom',
            'domain' : [('field_id','=', self.id)],
            'view_mode' : 'tree',
            'views' : [(False, 'tree')],
            'context' : {
                'default_field_id' : self.id
                }
            }
                