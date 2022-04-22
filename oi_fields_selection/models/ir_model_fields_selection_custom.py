'''
Created on Feb 19, 2019

@author: Zuhair Hammadi
'''
from odoo import models, fields, api, tools
import logging
_logger = logging.getLogger(__name__)

class IrModelFieldSelectionCustom(models.Model):
    _name = 'ir.model.fields.selection.custom'
    _description = 'Field Selection'
    _order = 'sequence,id'
    
    field_id = fields.Many2one('ir.model.fields', required = True, ondelete = 'cascade', index = True)
    value = fields.Char(required = True)
    name = fields.Char(required = True, translate = True)
    active = fields.Boolean(default = True)
    sequence = fields.Integer()
    
    _sql_constraints = [
        ('uk_value', 'unique(field_id, value)', 'Value must be unique!')
        ]
    
    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, '%s.%s - %s' % (record.field_id.model, record.field_id.name, record.value)))
        return res
    
    @api.model
    @tools.ormcache_context('field_id', keys=('lang',))
    def _get_selection(self, field_id):
        if field_id not in self._get_custom_fields_selection():
            return
        self.flush(['value', 'name'])
        records = self.search([('field_id','=', field_id), ('active','=', True)])
        return [(record.value, record.name) for record in records]  
    
    @api.model
    @tools.ormcache()
    def _get_custom_fields_selection(self):
        cr = self._cr
        if tools.table_exists(cr, self._table):
            cr.execute("select distinct field_id from ir_model_fields_selection_custom where active")
            return set(row[0] for row in cr.fetchall())
        return []
            
    @api.model_create_multi
    @api.returns('self', lambda value:value.id)
    def create(self, vals_list):
        self.clear_caches()
        return super(IrModelFieldSelectionCustom, self).create(vals_list)
        
    def unlink(self):
        self.clear_caches()
        return super(IrModelFieldSelectionCustom, self).unlink()
        
    def write(self, vals):
        self.clear_caches()
        return super(IrModelFieldSelectionCustom, self).write(vals)
    