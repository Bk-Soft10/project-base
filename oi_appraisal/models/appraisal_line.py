'''
Created on Nov 13, 2018

@author: Zuhair Hammadi
'''
from odoo import models, fields, api, SUPERUSER_ID,_
from odoo.exceptions import ValidationError

class AppraisalLines(models.Model):    
    _name = 'appraisal.line'
    _description = 'Appraisal Line'
    _order = 'sequence,id'
    
    appraisal_id = fields.Many2one('appraisal', required = True, ondelete='cascade')
    section_id = fields.Many2one('appraisal.section', required=True)    
    question_id = fields.Many2one('appraisal.question', readonly = True)
    name= fields.Char(required = True)
    description = fields.Text()
    weight = fields.Float('Weight', default=1)
    
    rate_type_id = fields.Many2one('appraisal.rate', string='Rating Type', compute = '_calc_rate_type_id')
    manager_rating_id = fields.Many2one('appraisal.rate.line', string='Manager Rating', domain="[('rate_type_id','=',rate_type_id)]")
    employee_rating_id = fields.Many2one('appraisal.rate.line', string='Employee Rating', domain="[('rate_type_id','=',rate_type_id)]")
    
    value = fields.Float('Rating in Percentage', compute = '_calc_value', store = True)
    
    sequence = fields.Integer()
    comments = fields.Text()
    
    manager_rating_enabled = fields.Boolean(compute = '_calc_rating_enabled')
    employee_rating_enabled = fields.Boolean(compute = '_calc_rating_enabled')
    update_enabled = fields.Boolean(compute = '_calc_update_enabled')
    
    parent_line_id = fields.Many2one('appraisal.line', string='Parent Objective')
    parent_id = fields.Many2one(related='appraisal_id.parent_id', readonly = True)
    required_parent_line_id = fields.Boolean(compute = '_calc_required_parent_line_id') 
    
    kpi = fields.Text('KPI/Measure')
    target_date = fields.Date()
    employee_evidence = fields.Text()
    manager_evidence = fields.Text()
            
    _sql_constraints = [
        ('name_uniq', 'unique(appraisal_id, section_id, name)', 'Question should be unique'),
    ]        
    
    @api.depends('question_id.rate_type_id','section_id.rate_type_id')
    def _calc_rate_type_id(self):
        for record in self:
            record.rate_type_id = record.question_id.rate_type_id or record.section_id.rate_type_id
    
    @api.depends('section_id.user_questions_enabled_states', 'section_id.enable_user_questions', 'appraisal_id.state')
    def _calc_update_enabled(self):
        for record in self:
            if record.section_id.user_questions_enabled_states:
                states = record.section_id.user_questions_enabled_states.split(',')
                record.update_enabled = record.section_id.enable_user_questions and record.appraisal_id.state in states
            else:
                record.update_enabled = True
                
    
    @api.depends('appraisal_id.parent_id', 'section_id')
    def _calc_required_parent_line_id(self):
        for record in self:
            record.required_parent_line_id = bool(record.appraisal_id.parent_id and record.section_id.required_parent_questions)
    
    @api.depends('manager_rating_id.value', 'section_id.rate_type_id.max_value')
    def _calc_value(self):
        for record in self:
            if record.rate_type_id.max_value != 0.0:
                record.value = record.manager_rating_id.value * 100 / record.rate_type_id.max_value
            else:
                record.value = 0.0
    
    @api.depends('appraisal_id.employee_id')
    def _calc_rating_enabled(self):
        for record in self:
            manager_rating_enabled = record.appraisal_id.employee_id.parent_id.user_id == self.env.user or not record.appraisal_id.employee_id.parent_id or self._uid == SUPERUSER_ID
            employee_rating_enabled = record.section_id.employee_rating and (record.appraisal_id.employee_id.user_id == self.env.user or self._uid == SUPERUSER_ID)
            if record.section_id.manager_rating_enabled_states:
                states = record.section_id.manager_rating_enabled_states.split(',')
                if record.appraisal_id.state not in states:
                    manager_rating_enabled = False
            if record.section_id.employee_rating_enabled_states:
                states = record.section_id.employee_rating_enabled_states.split(',')
                if record.appraisal_id.state not in states:
                    employee_rating_enabled = False                
            record.manager_rating_enabled = manager_rating_enabled
            record.employee_rating_enabled = employee_rating_enabled
                
    @api.constrains('question_id', 'section_id')
    def _check_question_id(self):
        for record in self:
            if not record.question_id and not record.section_id.enable_user_questions:
                raise ValidationError(_('Section not allowed user questions'))
            if record.question_id and record.question_id.section_id != record.section_id:
                raise ValidationError(_('Invalid Question/Section'))            
    
    
    def _check_lines_locked(self):
        if any(self.mapped('appraisal_id.is_lines_locked')):
            raise ValidationError(_('Appraisal Lines Locked'))
            
    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def create(self, vals_list):
        records = super(AppraisalLines, self).create(vals_list)
        records._check_lines_locked()            
        return records
    
    
    def write(self, vals):
        res = super(AppraisalLines, self).write(vals)
        self._check_lines_locked()
        return res
    
    
    def unlink(self):
        self._check_lines_locked()
        for record in self:
            if record.appraisal_id.state != 'draft' and not record.update_enabled:
                raise ValidationError(_('Line cannot be deleted'))
        return super(AppraisalLines, self).unlink()