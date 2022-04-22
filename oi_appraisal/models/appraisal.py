'''
Created on Nov 13, 2018

@author: Zuhair Hammadi
'''
from odoo import models, fields, api, _
from collections import defaultdict
from odoo.exceptions import Warning, ValidationError
import re
class Appraisal(models.Model):    
    _name = 'appraisal'    
    _description='Employee Appraisal'
    _inherit = ['approval.record', 'mail.thread', 'mail.activity.mixin']
    
    name = fields.Char('Number', required = True, readonly = True, default = _('New'))
    employee_id = fields.Many2one('hr.employee', string='Employee', required = True, readonly = True)
    company_id = fields.Many2one(related='employee_id.company_id', readonly = True)
    
    department_id = fields.Many2one('hr.department', string='Department', compute = '_calc_employee_related', store = True)
    job_id = fields.Many2one('hr.job', string='Job Position', compute = '_calc_employee_related', store = True)
    manager_id = fields.Many2one('hr.employee', string='Manager', compute = '_calc_employee_related', store = True)    
    
    parent_id = fields.Many2one('appraisal', string='Manager Appraisal', compute = '_calc_parent_id', store = True)
    child_ids = fields.One2many('appraisal', 'parent_id', string='Subordinates Appraisal')
    
    template_id = fields.Many2one('appraisal.template', string='Template', required = True, readonly = True)
    batch_id = fields.Many2one('appraisal.batch', string='Appraisal Batch', required = True, readonly = True, ondelete='cascade')
    year = fields.Char(related='batch_id.year', readonly=True, store=True)
    
    line_ids = fields.One2many('appraisal.line', 'appraisal_id', states={'done' : [('readonly', True)], 'rejected' : [('readonly', True)]})
    result = fields.Float('Final Result', group_operator="avg", compute = '_calc_results', store = True, track_visibility = True)
    result_title = fields.Text('Final Result Title', compute = '_calc_results', store = True, track_visibility = True)
    
    lines_locked = fields.Boolean(groups="base.group_system")
    is_lines_locked = fields.Boolean(compute = '_calc_lines_enabled')
    
    comments = fields.Text(states={'done' : [('readonly', True)], 'rejected' : [('readonly', True)]})
    
    _sql_constraints = [
        ('batch_emp_uniq', 'unique(employee_id,batch_id)', 'This employee already has an appraisal on this batch!'),
    ]    
    
    def _onchange_eval(self, field_name, onchange, result):
        res = super(Appraisal, self)._onchange_eval(field_name, onchange, result)
        if field_name and re.match('^x_previous_\d+$', field_name):
            line_id = self[field_name]
            if line_id:
                section_id = int(field_name[11:])
                section = self.env['appraisal.section'].browse(section_id)
                if section.lines_field_id.name:
                    self[section.lines_field_id.name] += self.env['appraisal.line'].new({'name' : line_id.name,
                                                                                         'description' : line_id.description,
                                                                                         'weight' : line_id.weight,                                                                                          
                                                                                         'section_id' : section_id})
                self[field_name] = False
        return res
    
    @api.model
    def _after_approval_states(self):
        return  [('done', 'Completed'), ('rejected', 'Rejected')]    
    
    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def create(self, vals_list):
        for vals in vals_list:
            employee = self.env['hr.employee'].browse(vals['employee_id'])
            vals['name'] = self.env['ir.sequence'].with_context(force_company = employee.company_id.id).next_by_code(self._name)
        return super(Appraisal, self).create(vals_list)
    
    
    def unlink(self):
        if any(self.filtered(lambda record : record.state!='draft')):
            raise Warning(_('You can delete draft status only'))
        return super(Appraisal, self).unlink()    
    
    @api.depends('manager_id', 'batch_id')
    def _calc_parent_id(self):              
        for record in self:
            record.parent_id = self.sudo().search([('employee_id', '=', record.manager_id.id), ('batch_id', '=', record.batch_id.id)], limit =1)
        
    @api.depends('lines_locked', 'state')
    def _calc_lines_enabled(self):
        for record in self:
            if record.id:
                lines_locked = self._get_sql_value('select lines_locked from appraisal where id=%s', [record.id])
                record.is_lines_locked = record.state in ['done', 'rejected'] or lines_locked
            else:
                record.is_lines_locked = False
                
    @api.depends('line_ids.value','line_ids.weight', 'line_ids.section_id.weight', 'line_ids.section_id.rate_type_id.lines_ids')
    def _calc_results(self):    
        for record in self:
            weight = defaultdict(float)
            value = defaultdict(float)
            section_weight = dict()
            for line in record.line_ids:
                result_field = line.section_id.result_field_id.name
                weight[result_field] += line.weight    
                value[result_field] += line.weight * line.value
                section_weight[result_field] = line.section_id.with_context(template_id = record.template_id.id).weight4tempalte
            total_weight = 0
            total_value = 0
            
            for field in self.env['ir.model.fields'].sudo().search([('model','=', self._name), ('name','=ilike', 'x_result_%')]):
                weight.setdefault(field.name, 0)
                value.setdefault(field.name, 0)
                section_weight.setdefault(field.name, 0)
            
            for result_field in weight.keys():
                record[result_field] = weight[result_field] and value[result_field] / weight[result_field]
                total_weight += section_weight[result_field]
                total_value += record[result_field] * section_weight[result_field]
            record.result = total_weight and total_value / total_weight
            if record.result:
                rate_type_id = record.template_id.rate_type_id or record.mapped('line_ids.section_id.rate_type_id')[:1]                
                max_value = rate_type_id.max_value
                if max_value:
                    multiplier = 100 / max_value
                    value = round(record.result / multiplier)
                    record.result_title= rate_type_id.lines_ids.filtered(lambda line : line.value <= value).sorted('value', reverse = True)[:1].name
            else:
                record.result_title = False
            
    @api.depends('employee_id')
    def _calc_employee_related(self):
        for record in self:
            record.department_id = record.employee_id.department_id
            record.job_id = record.employee_id.job_id
            record.manager_id = record.employee_id.parent_id
                        
    @api.depends('template_id.sections_ids')
    def _calc_section_enabled(self):
        for record in self:
            sections_ids = record.template_id.sections_ids
            for section in self.env['appraisal.section'].search([]):
                if section.enabled_field_id.name:               
                    record[section.enabled_field_id.name] = section in sections_ids    
    
    @api.depends('state')
    def _calc_previous_enabled(self):  
        for record in self:
            for section in self.env['appraisal.section'].search([]):
                if section.previous_field_enabled_id.name and section.user_questions_enabled_states and section.show_previous_objective:   
                    states = section.user_questions_enabled_states.split(',')            
                    record[section.previous_field_enabled_id.name] = record.state in states
                else:
                    record[section.previous_field_enabled_id.name] = False
            
                    
    @api.depends('parent_id')
    def _calc_parent_lines(self):
        for record in self:
            parent_lines_ids = record.sudo().parent_id.line_ids
            for section in self.env['appraisal.section'].search([]):
                fname = section.parent_lines_field_id.name
                if fname:               
                    record[fname] = parent_lines_ids.filtered(lambda line : line.section_id == section)                        
    
    
    def _validate_employee_rating(self):
        for line in self.line_ids:
            if line.section_id.employee_rating and not line.employee_rating_id:
                raise ValidationError(_('Select Employee Rating for %s') % line.name)
                
    
    def _validate_manager_rating(self):
        for line in self.line_ids:
            if line.section_id.manager_rating and not line.manager_rating_id:
                raise ValidationError(_('Select Rating for %s') % line.name)                
                