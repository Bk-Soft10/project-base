'''
Created on Nov 1, 2017

@author: Zuhair Hammadi
'''
from odoo import models, api, fields, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError

class _Many2many(fields.Many2many):
    
    def _setup_regular_base(self, model):
        self.relation = '%s_%s_rel' % (model._table, self.name)
        return super(_Many2many, self)._setup_regular_base(model)

class ApprovalConfig(models.Model):
    _name = 'approval.config'
    _description = 'Approval Workflow Settings'
    _order = 'sequence,id'
    
    @api.model
    def _get_sequence(self):
        model_id = self._context.get('default_model_id') or 0
        self._cr.execute('select max(sequence) from %s where model_id =%s' % (self._table, model_id))
        sequence, = self._cr.fetchone()
        return (sequence or 0) + 10
            
    model_id = fields.Many2one('ir.model', string='Object', required = True, ondelete='cascade')
    
    model = fields.Char(related='model_id.model', readonly = True)
    model_name = fields.Char(related='model_id.name', readonly = True)

    state = fields.Char(required = True, copy = False)
    name = fields.Char(required = True, translate = True)
    active = fields.Boolean(default = True)
    sequence = fields.Integer(default = _get_sequence, required = True, copy = False)    
    
    group_ids = _Many2many('res.groups', string='Approval Groups', required = True)
    
    filter_condition = fields.Char('Filter Condition')
        
    condition = fields.Text(string='Required Condition', default = 'True', requried = True )
                
    template_ids = fields.Many2many('mail.template', string='Mail Templates')
    reject_template_ids = _Many2many('mail.template', string='Reject Mail Templates')
    
    auto_subscribe_users = fields.Boolean('Add followers', help='Add Approval Users to the record followers')
    
    auto_subscribe_users_enabled = fields.Boolean(compute = '_calc_auto_subscribe_users_enabled')
    
    schedule_activity = fields.Boolean('Schedule Activity', default = True)
    schedule_activity_field_id = fields.Many2one('ir.model.fields')
    schedule_activity_days = fields.Integer('Activity Days')
    
    schedule_activity_enabled = fields.Boolean('Hours', compute = '_calc_schedule_activity_enabled')
    
    post_approval_msg = fields.Boolean('Post Approval Message')
    post_reject_msg = fields.Boolean('Post Reject Message')
    
    before_script = fields.Text('Before Script', help='Script to Execute on Enter this State')
    after_script = fields.Text('After Script', help= 'Script to Execute after Exit this State')
    on_script = fields.Text('On Script', help= 'Script to Execute on Exit this State')
    
    reject_script = fields.Text('Reject Script', help= 'Script to Execute on Reject')
    
    approve_button_name = fields.Char(default = 'Approve', translate = True)
    approve_confirm_msg = fields.Char(default = 'Approve ?', translate = True)
    
    reject_button_name = fields.Char(default = 'Reject', translate = True)        
    reject_button_wizard = fields.Boolean(default = True)
    approve_button_wizard = fields.Boolean(default = False)
    reject_confirm_msg = fields.Char(default = 'Reject ?', translate = True)  
    
    escalation_ids = fields.One2many('approval.escalation', 'config_id', domain = ['|', ('active', '=', True), ('active', '=', False)])
    last_state_update_id = fields.Many2one('ir.model.fields', compute = '_calc_last_state_update_id')
    
    allow_forward = fields.Boolean()
    allow_return = fields.Boolean()
    allow_transfer = fields.Boolean()
    
    auto_approve = fields.Boolean('Automatic Approval')
    
    _sql_constraints = [
        ('state_uniq', 'unique (model_id, state)', 'The state should be unique !'),
        ('name_uniq', 'unique (model_id, name)', 'The name should be unique !'),       
    ]    
    
    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, '%s %s' % (record.model, record.state)))
        return res    
    
    @api.depends('model')
    def _calc_last_state_update_id(self):
        for record in self:
            record.last_state_update_id = self.env['ir.model.fields']._get(record.model, 'last_state_update')
                
    @api.depends('model_id')                   
    def _calc_auto_subscribe_users_enabled(self):
        for record in self:
            model = self.env[record.model_id.model]
            record.auto_subscribe_users_enabled = model._isinstance('mail.thread')        
            
    @api.depends('model_id')                   
    def _calc_schedule_activity_enabled(self):
        for record in self:
            model = self.env[record.model_id.model]
            record.schedule_activity_enabled = model._isinstance('mail.activity.mixin') and model._isinstance('mail.thread')
            
    @api.constrains('auto_subscribe_users')
    def _check_auto_subscribe_users(self):
        for record in self:
            if record.auto_subscribe_users and not record.auto_subscribe_users_enabled:
                raise ValidationError(_('Object must inherit mail.thread')) 
            
    @api.constrains('schedule_activity')
    def _check_schedule_activity(self):
        for record in self:
            if record.schedule_activity and not record.schedule_activity_enabled:
                raise ValidationError(_('Object must inherit mail.activity.mixin')) 
            
                                                                                                    
    def _get_next(self, record):
        if not self:
            model_id = self.env['ir.model']._get_id(record._name)            
            return self.search([('active','=', True), ('model_id','=', model_id)], limit = 1)._next(record)
        return self._next(record, True)
    
    def _next(self, record, force = False):
        if not self:
            return self
        
        self.ensure_one()
                
        if not force:
            result = safe_eval(self.condition, record._get_eval_context())
            if result:
                return self
        
        return self.search([('model_id','=', self.model_id.id), ('active','=', True), '|', ('sequence', '>', self.sequence), '&', ('sequence', '=', self.sequence), ('id', '>', self.id)], limit = 1)._next(record)    
    
    
    @api.model
    def _update_approval_activity(self):
        for group in self.read_group([('schedule_activity','=', True)], ['model_id'], ['model_id']):
            model = self.env['ir.model'].browse(group['model_id'][0]).model
            states = self.search(group['__domain']).mapped('state')
            for record in self.env[model].search([('state', 'in', states)]):
                record._update_approval_activity()
                
    @api.model            
    def _run_update_approval_activity(self):
        try:
            with self.env.cr.savepoint():
                self.env.ref('oi_workflow.cron_update_approval_activity').write({'nextcall' : fields.Datetime.now()})
        except:
            pass
            
    @api.model_create_multi
    @api.returns('self', lambda value:value.id)
    def create(self, vals_list):
        self.clear_caches()
        return super(ApprovalConfig, self).create(vals_list)
    
    def write(self, vals):
        self.clear_caches()
        return super(ApprovalConfig, self).write(vals)
    
    def unlink(self):
        self.clear_caches()
        return super(ApprovalConfig, self).unlink()            