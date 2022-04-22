'''
Created on Feb 19, 2019

@author: Zuhair Hammadi
'''
from odoo import fields
from odoo.fields import resolve_mro
    
super_description_selection = fields.Selection._description_selection
super_get_values = fields.Selection.get_values
super_setup_attrs = fields.Selection._setup_attrs

def _get_selection(self, env):
    if 'ir.model.fields.selection.custom' not in env:
        return
    field_id = env['ir.model.fields']._get_id(self.model_name, self.name)
    return env['ir.model.fields.selection.custom']._get_selection(field_id)

def _get_approval_selection(self, env):
    if 'approval.record' not in env:
        return
    model = env[self.model_name]
    if model._isinstance('approval.record') and self.name =='state':
        return model._get_state()
    
def _description_selection(self, env):
    custom_selection = _get_selection(self, env)
    if custom_selection:
        return custom_selection
    
    approval_selection = _get_approval_selection(self, env)
    if approval_selection:
        return approval_selection
        
    return super_description_selection(self, env)

def get_values(self, env):
    custom_selection = _get_selection(self, env)
    if custom_selection:
        return [sel[0] for sel in custom_selection]
    
    approval_selection = _get_approval_selection(self, env)
    if approval_selection:
        return list(map(lambda item : item[0], approval_selection))
                
    return super_get_values(self, env)

def _setup_attrs(self, model, name):
    dynamic_selection = False
    
    for field in reversed(resolve_mro(model, name, self._can_setup_from)):
        if 'selection' in field.args:
            if not isinstance(field.args['selection'], list):
                dynamic_selection = True
                
        if 'selection_add' in field.args and dynamic_selection:            
            field.args.pop('selection_add')
            
    return super_setup_attrs(self, model, name)

fields.Selection._description_selection = _description_selection
fields.Selection.get_values = get_values
fields.Selection._setup_attrs = _setup_attrs