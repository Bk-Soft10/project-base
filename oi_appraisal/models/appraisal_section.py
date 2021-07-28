'''
Created on Nov 13, 2018

@author: Zuhair Hammadi
'''
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_view_arch = """
<data>
<notebook position="before"> 
    <group name="parent_questions_%(id)s" string="Parent %(name)s" invisible="%(hide_parent_questions)d" >
        <field name="%(parent_lines_field)s" nolabel="1">
            <tree>                
                <field name="name" />
            </tree>
            <form>
                <field name="name" />
            </form>
        </field>
    </group>
</notebook>

%(result_field)s
    <notebook position="inside"> 
        <page string="%(name)s" name="page_section_%(id)s" attrs="{'invisible': [('%(enabled_field)s','=',False)]}">
            <group>
                <field name="%(enabled_field)s" invisible="1"/>
            </group>
            <group>
                <field name="%(lines_field)s" nolabel="1" context="{'default_section_id': %(id)s}" attrs="{'readonly': [('is_lines_locked','=', True)]}"> 
                    <tree editable="bottom" create="%(enable_user_questions)d" delete="%(enable_user_questions)d"> 
                        <field name="id" invisible="1"/>
                        <field name="section_id" invisible="1"/>
                        <field name="rate_type_id" invisible="1"/>
                        <field name="manager_rating_enabled" invisible="1"/>
                        <field name="employee_rating_enabled" invisible="1"/>
                        <field name="required_parent_line_id" invisible="1"/>
                        <field name="update_enabled" invisible="1"/>
                        <field name="sequence" invisible="%(not_enable_user_questions)d" widget="handle"/>
                        <field name="name" attrs="{'readonly' : [('update_enabled', '=', False)]}" />                  
                        <field name="parent_line_id" options="{'no_create_edit' : True}" invisible="%(hide_parent_questions_line)d" 
                            attrs="{'required' : [('required_parent_line_id', '=', True)]}" 
                            domain="[('appraisal_id','=', parent.parent_id), ('section_id','=', %(id)d)]" />   
                        <field name="kpi" invisible ="%(hide_user_kpi)d" 
                            attrs="{'readonly' : [('update_enabled', '=', False)]}" />
                        <field name="target_date" invisible ="%(hide_target_date)d" 
                            attrs="{'readonly' : [('update_enabled', '=', False)]}" />                            
                        <field name="description" invisible ="%(hide_description)d" attrs="{'readonly' : [('update_enabled', '=', False)]}" />                                                  
                        <field name="weight" invisible ="%(hide_user_weight)d" attrs="{'readonly' : [('update_enabled', '=', False)]}" />
                        <field name="employee_rating_id" invisible="%(not_employee_rating)d" 
                            attrs="{'readonly': [('employee_rating_enabled','=',False)]}" 
                            options="{'no_create_edit' : True}" />
                        <field name="employee_evidence" invisible="%(hide_employee_evidence)d" 
                            attrs="{'readonly': [('employee_rating_enabled','=',False)]}" 
                            />                            
                        <field name="manager_rating_id" invisible="%(not_manager_rating)d" 
                            attrs="{'readonly': [('manager_rating_enabled','=',False)]}" 
                            options="{'no_create_edit' : True}" />
                        <field name="manager_evidence" invisible="%(hide_manager_evidence)d" 
                            attrs="{'readonly': [('manager_rating_enabled','=',False)]}" 
                            />                            
                        <field name="comments" invisible="%(hide_user_comments)d" />
                    </tree>
                </field>
            </group> 
            <group invisible="%(hide_previous_objective)d" class="oe_edit_only">
                <field name="%(previous_field_enabled)s" invisible="1"  />
                <field name="%(previous_field)s" options="{'no_create_edit' : True}" attrs="{'invisible' : [('%(previous_field_enabled)s', '=', False)]}" on_change="1" 
                    domain="[('section_id','=', %(id)d), ('appraisal_id.employee_id.user_id','=', uid), ('appraisal_id','!=', active_id)]"  />
            </group>
        </page> 
    </notebook>
</data>
"""

def remove_unchange(vals, record):
    for fname in list(vals):
        if vals[fname] == record[fname]:
            vals.pop(fname)
    

class AppraisalSection(models.Model):    
    _name = 'appraisal.section'
    _description = 'Appraisal Section'
    _order = 'sequence,id'

    name = fields.Char(required=True)  
    code = fields.Char()  
    active= fields.Boolean(default=True)
    rate_type_id = fields.Many2one('appraisal.rate', 'Appraisal Rating Type', required = True)
    
    employee_rating = fields.Boolean('Allow Employee Rating')
    manager_rating = fields.Boolean('Allow Manager Rating', default=True)   
    enable_user_questions = fields.Boolean('User Defined Objectives')
    enable_user_weight = fields.Boolean('User Defined Weight')    
    enable_user_comments = fields.Boolean('User Comments')
    enable_user_kpi = fields.Boolean('User KPI/Measure')
    show_description = fields.Boolean('Show Description')
    
    show_parent_questions = fields.Boolean('Show Parent Objectives')
    show_parent_questions_line = fields.Boolean('Show Parent Objectives in Line')
    required_parent_questions = fields.Boolean('Required Parent Objectives')
    
    show_section_result = fields.Boolean('Show Section Result', default=True)
    
    show_target_date = fields.Boolean()
    show_employee_evidence = fields.Boolean()
    show_manager_evidence = fields.Boolean()
    
    weight = fields.Float(default=1)
    weight4tempalte = fields.Float(compute = '_calc_weight4tempalte')
    weight_percent = fields.Float('Weight %', compute = '_calc_weight_percent')  
    sequence = fields.Integer()
    
    question_ids = fields.One2many('appraisal.question','section_id', string='Questions')
    question_count = fields.Integer(compute = '_calc_question_count')

    lines_field_id = fields.Many2one('ir.model.fields')
    parent_lines_field_id = fields.Many2one('ir.model.fields')
    enabled_field_id = fields.Many2one('ir.model.fields')    
    result_field_id = fields.Many2one('ir.model.fields')
    previous_field_id = fields.Many2one('ir.model.fields')
    previous_field_enabled_id = fields.Many2one('ir.model.fields')
    section_view_id = fields.Many2one('ir.ui.view')        
    
    manager_rating_enabled_states = fields.Char()
    employee_rating_enabled_states = fields.Char()
    user_questions_enabled_states = fields.Char()
    
    manager_rating_enabled_states_ids = fields.Many2many('appraisal.states', string='Manager Rating Enabled States', compute = '_calc_manager_rating_enabled_states_ids', inverse = '_set_manager_rating_enabled_states')
    employee_rating_enabled_states_ids = fields.Many2many('appraisal.states', string='Employee Rating Enabled States', compute = '_calc_employee_rating_enabled_states_ids', inverse = '_set_employee_rating_enabled_states' )
    user_questions_enabled_states_ids = fields.Many2many('appraisal.states', string='Defined Objectives Enabled States', compute = '_calc_user_questions_enabled_states_ids', inverse = '_set_user_questions_enabled_states' )
        
    template_ids = fields.Many2many('appraisal.template', string='Appraisal Template')
    
    show_previous_objective = fields.Boolean('Show Previous Objective')
    
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Name must be unique!'),
    ]
    
    @api.depends('weight')
    def _calc_weight4tempalte(self):
        template_id = self._context.get('template_id') or []
        template = self.env['appraisal.template'].browse(template_id)
        for record in self:
            sec_wt = template.weight_ids.filtered(lambda w : w.section_id == record)
            if sec_wt:
                record.weight4tempalte = sec_wt.weight
            else:
                record.weight4tempalte = record.weight
    
    @api.depends('manager_rating_enabled_states')
    def _calc_manager_rating_enabled_states_ids(self):
        for record in self:
            if record.manager_rating_enabled_states:
                states = record.manager_rating_enabled_states.split(',')
                record.manager_rating_enabled_states_ids = self.env['appraisal.states'].search([('state','in', states)])
            else:
                record.manager_rating_enabled_states_ids = False
    
    @api.depends('employee_rating_enabled_states')
    def _calc_employee_rating_enabled_states_ids(self):
        for record in self:
            if record.employee_rating_enabled_states:
                states = record.employee_rating_enabled_states.split(',')
                record.employee_rating_enabled_states_ids = self.env['appraisal.states'].search([('state','in', states)])
            else:
                record.employee_rating_enabled_states_ids = False
                
    @api.depends('user_questions_enabled_states')
    def _calc_user_questions_enabled_states_ids(self):
        for record in self:
            if record.user_questions_enabled_states:
                states = record.user_questions_enabled_states.split(',')
                record.user_questions_enabled_states_ids = self.env['appraisal.states'].search([('state','in', states)])        
            else:
                record.user_questions_enabled_states_ids = False        
                
    def _set_manager_rating_enabled_states(self):
        for record in self:
            record.manager_rating_enabled_states = ','.join(record.manager_rating_enabled_states_ids.mapped('state'))
            
    def _set_employee_rating_enabled_states(self):
        for record in self:
            record.employee_rating_enabled_states = ','.join(record.employee_rating_enabled_states_ids.mapped('state'))
            
    def _set_user_questions_enabled_states(self):
        for record in self:
            record.user_questions_enabled_states = ','.join(record.user_questions_enabled_states_ids.mapped('state'))
                    
    
    @api.depends('question_ids')
    def _calc_question_count(self):
        for record in self:
            record.question_count = len(record.question_ids)
    
    @api.depends('weight4tempalte')
    def _calc_weight_percent(self):
        template_id = self._context.get('template_id')
        if not template_id:
            for record in self:
                record.weight_percent = False
            return
        template = self.env['appraisal.template'].browse(template_id)
        total = sum(template.mapped('sections_ids.weight4tempalte'))
        for record in self:            
            record.weight_percent = total and record.weight4tempalte * 100 / total        
    
    @api.constrains('manager_rating_enabled_states', 'employee_rating_enabled_states')
    def check_manager_rating_enabled_states(self):
        appraisal_states = set(map(lambda state : state[0], self.env['appraisal']._get_state()))        
        
        def check_states(states):
            if not states:
                return
            states = states.split(',')
            for state in states:
                if state not in appraisal_states:
                    raise ValidationError('Invalid State [%s]' % state)
            
        for record in self:
            check_states(record.manager_rating_enabled_states)
            check_states(record.employee_rating_enabled_states)
                    
        
    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def create(self, vals_list):
        records = super(AppraisalSection, self).create(vals_list)
        for record in records:
            record._create_section_fields()
            record._create_section_view()
        return records
    
    
    def write(self, vals):
        res = super(AppraisalSection, self).write(vals)
        for record in self:
            record._create_section_fields()
            record._create_section_view()
        return res
    
    
    def unlink(self):
        field_ids = self.env['ir.model.fields']
        for name, field in self._fields:
            if field.type == 'many2one' and field.comodel_name == 'ir.model.fields':
                field_ids += self.mapped(name)
        view_ids = self.mapped('section_view_id').sudo()
        view_ids.write({'active': False})
        
        res = super(AppraisalSection, self).unlink()
        
        field_ids.sudo().unlink()
        view_ids.unlink()
        return res
        
    
    def _get_view_arch(self):
        self.ensure_one()
        vals = {
            'name' : self.name,
            'result_field' : '',
            'enabled_field' : self.enabled_field_id.name,
            'lines_field' : self.lines_field_id.name,
            'id' : self.id,
            'enable_user_questions' : self.enable_user_questions,
            'not_enable_user_questions' : not self.enable_user_questions,
            'not_employee_rating' : not self.employee_rating,
            'not_manager_rating' : not self.manager_rating,
            'weight_field' : '',
            'comments_field' : '',
            'hide_parent_questions' : not self.show_parent_questions,
            'parent_lines_field' : self.parent_lines_field_id.name,
            'hide_parent_questions_line' : not self.show_parent_questions_line,
            'hide_description' : not self.show_description,
            'hide_user_weight' : not self.enable_user_weight,
            'hide_user_comments' : not self.enable_user_comments,
            'hide_user_kpi' : not self.enable_user_kpi,
            'hide_previous_objective' : not self.show_previous_objective,
            'previous_field' : self.previous_field_id.name,
            'previous_field_enabled' : self.previous_field_enabled_id.name,
            'hide_target_date' : not self.show_target_date,
            'hide_employee_evidence' : not self.show_employee_evidence,
            'hide_manager_evidence' : not self.show_manager_evidence
            }
        if self.show_section_result:
            vals['result_field'] = """
    <field name="batch_id" position="after">
            <field name ="%s" attrs="{'invisible': [('%s','=',False)]}"/> 
    </field>            
            """ % (self.result_field_id.name, self.enabled_field_id.name)
        return _view_arch % vals
    
    @api.model
    def _update_sections_view(self):
        for record in self.search([]):
            record._create_section_fields()
            record._create_section_view()        
    
    
    def _create_section_view(self):
        self = self.sudo()
        self.ensure_one()
        vals = {
            'arch' : self._get_view_arch(),
            'priority' : self.sequence,
            }
        if self.section_view_id:
            remove_unchange(vals, self.section_view_id)
            self.section_view_id.write(vals)
        else:
            vals.update({
                'name' : 'appraisal.form.section.%s' % self.id,
                'model' : 'appraisal',
                'type' : 'form',
                'inherit_id' : self.env.ref('oi_appraisal.view_appraisal_form').id
                })
            self.section_view_id = self.env['ir.ui.view'].create(vals)
            

    
    def _create_section_fields(self):
        self = self.sudo()
        self.ensure_one()
        model_id = self.env['ir.model']._get_id('appraisal')
        vals = {            
            'field_description' : self.name                 
            }
        if self.lines_field_id:
            pass
        else:
            vals.update({
                'name' : 'x_line_ids_%s' % (self.id),
                'model_id' : model_id,
                'ttype':'one2many',
                'relation':'appraisal.line',
                'relation_field': 'appraisal_id',
                'domain': "[('section_id','=',%s)]" %(self.id)       
                })
            self.lines_field_id=self.env['ir.model.fields'].create(vals)
            
        vals = {
            'field_description': 'Parent %s' % self.name,
            }
                
        if self.parent_lines_field_id:
            remove_unchange(vals, self.parent_lines_field_id)
            self.parent_lines_field_id.write(vals)
        else:
            vals.update({
                'name' : 'x_parent_line_ids_%s' % (self.id),
                'model_id': model_id, 
                'ttype':'many2many',
                'relation':'appraisal.line',
                'depends':'template_id.sections_ids,parent_id',
                'compute':'self._calc_parent_lines()',
                'readonly' : True,
                'store' : False
                })
            self.parent_lines_field_id = self.env['ir.model.fields'].create(vals)
            
        vals = {
            'field_description': '%s Enabled' % self.name,
            }
        if self.enabled_field_id:
            remove_unchange(vals, self.enabled_field_id)
            self.enabled_field_id.write(vals)
        else:
            vals.update({
                'name' : 'x_section_enabled_%s' % (self.id),
                'model_id': model_id, 
                'ttype':'boolean',
                'depends':'template_id.sections_ids',
                'compute':'self._calc_section_enabled()',
                'readonly' : True,
                'store' : True
                })
            self.enabled_field_id = self.env['ir.model.fields'].create(vals)
            
        vals = {
            'field_description': '%s Result' % self.name,
            }
        if self.result_field_id:
            remove_unchange(vals, self.result_field_id)
            self.result_field_id.write(vals)
        else:
            vals.update({
                'name' : 'x_result_%s' % (self.id),
                'model_id' : model_id,
                'ttype':'float',
                'depends': 'line_ids.value,line_ids.weight,line_ids.section_id.weight',
                'compute':'self._calc_results()',
                'readonly' : True,
                'store' : True                
                })
            self.result_field_id=self.env['ir.model.fields'].create(vals)
            
        vals = {
            'field_description': 'Add Previous %s' % self.name,
            }
            
        if self.previous_field_id:
            remove_unchange(vals, self.previous_field_id)
            self.previous_field_id.write(vals)
        else:
            vals.update({
                'name' : 'x_previous_%s' % (self.id),
                'model_id' : model_id,
                'ttype':'many2one',
                'relation':'appraisal.line',
                'readonly' : False,
                'store' : False            
                })
            self.previous_field_id=self.env['ir.model.fields'].create(vals)
            
        vals = {
            'field_description': 'Previous %s Enabled' % self.name,
            }
                    
        if self.previous_field_enabled_id:
            remove_unchange(vals, self.previous_field_enabled_id)
            self.previous_field_enabled_id.write(vals)
        else:
            vals.update({
                'name' : 'x_previous_enabled_%s' % (self.id),
                'model_id' : model_id,
                'ttype':'boolean',
                'readonly' : True,
                'depends': 'state,line_ids.section_id.show_previous_objective',
                'compute':'self._calc_previous_enabled()',
                'store' : False            
                })
            self.previous_field_enabled_id=self.env['ir.model.fields'].create(vals)
            