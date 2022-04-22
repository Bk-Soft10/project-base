'''
Created on Nov 1, 2017

@author: Zuhair Hammadi
'''
from odoo import models, fields, api,tools, SUPERUSER_ID, _
from odoo.tools.safe_eval import safe_eval
from datetime import timedelta
from odoo.exceptions import Warning, AccessError, ValidationError
from dateutil.relativedelta import relativedelta

import logging
import json
_logger = logging.getLogger(__name__)

class ApprovalRecord(models.AbstractModel):
    _name ='approval.record'
    _description = 'Approval Record'

    @api.model
    @tools.ormcache_context(keys=('lang',))
    def _get_state(self):
        return (self._before_approval_states_custom() or  self._before_approval_states()) + \
            self._approval_states() + \
            (self._after_approval_states_custom() or self._after_approval_states())
    
    state = fields.Selection(_get_state, string='Status', copy = False, tracking = True, required = True,group_expand ='_expand_states')
    
    state_id = fields.Many2one('approval.config', compute = '_calc_state_id', search = '_search_state_id', string='Status Settings')
    state_name = fields.Char(compute ='_calc_state_name')
    
    button_draft_enabled = fields.Boolean(compute ='_calc_button_draft_enabled')
    button_approve_enabled = fields.Boolean(compute ='_calc_button_enabled')        
    
    approval_user_ids = fields.Many2many('res.users', string='Waiting User Approval', compute = '_calc_approval_user_ids', search ='_search_approval_user_ids')
    #without admin
    approval_user2_ids = fields.Many2many('res.users', string='Waiting User Approval (Without OdooBot)', compute = '_calc_approval_user_ids')
    
    approval_partner_ids = fields.Char(string='Waiting Partner IDs Approval', compute = '_calc_approval_user_ids')
    
    user_can_approve = fields.Boolean(compute = '_calc_approval_user_ids')
    
    approval_emp_emails = fields.Char(compute = '_calc_approval_emp_emails')
    
    document_user_id = fields.Many2one('res.users', compute = '_calc_document_user_id')    
    
    waiting_approval = fields.Boolean(compute = '_calc_waiting_approval', search= '_search_waiting_approval')
    
    needaction_partner_ids = fields.Char(compute = '_calc_needaction_partner_ids')
    
    approval_emails = fields.Char(compute = '_calc_approval_emails')
    
    log_ids = fields.Many2many('approval.log', string='Status Log', compute = '_calc_log_ids')    
    
    approve_button_name = fields.Char(related='state_id.approve_button_name', readonly = True)
    approve_confirm_msg = fields.Char(related='state_id.approve_confirm_msg', readonly = True)
    
    reject_button_name = fields.Char(related='state_id.reject_button_name', readonly = True)    
    reject_button_wizard = fields.Boolean(related='state_id.reject_button_wizard', readonly = True)
    approve_button_wizard = fields.Boolean(related='state_id.approve_button_wizard', readonly = True)
    reject_confirm_msg = fields.Char(related='state_id.reject_confirm_msg', readonly = True)  
    
    last_state_update = fields.Datetime(default = fields.Datetime.now, readonly = True, required = True)
    workflow_states = fields.Char(compute = '_calc_workflow_states')
        
    button_forward_enabled = fields.Boolean(compute = '_calc_button_enabled')
    button_return_enabled = fields.Boolean(compute = '_calc_button_enabled')
    button_transfer_enabled = fields.Boolean(compute = '_calc_button_enabled')
        
    @api.model
    @tools.ormcache()
    def _get_approval_models(self):
        models = []
        for model_name,model in self.env.items():
            if model._isinstance('approval.record') and not model._abstract:
                models.append(model_name) 
        return models               
    
    @api.model
    def default_get(self, fields_list):
        res = super(ApprovalRecord, self).default_get(fields_list)
        if not fields_list or 'state' in fields_list:
            if 'state' not in res:
                res['state'] = self._get_draft_state()
        return res
            
    def _calc_log_ids(self):
        model_id = self.env['ir.model']._get_id(self._name)
        for record in self:            
            log_ids = self.env['approval.log'].search([('model_id','=', model_id), ('record_id','=', record.id)])
            record.log_ids = log_ids                        
    
    @api.depends('write_uid')    
    def _calc_document_user_id(self):
        if 'employee_id' in self:
            for record in self:
                record.document_user_id = record.employee_id.user_id
        elif 'create_uid' in self:
            for record in self:
                record.document_user_id = record.create_uid                                        
    
    @api.depends('approval_user2_ids')
    def _calc_needaction_partner_ids(self):
        for record in self:
            record.needaction_partner_ids = '[(6,0, %s)]' % record.mapped('approval_user2_ids.partner_id.id')
    
    @api.depends('approval_user2_ids')
    def _calc_approval_emails(self):
        for record in self:
            record.approval_emails = ';'.join(filter(None,record.mapped('approval_user2_ids.employee_ids.work_email')))
    
    @api.depends('state')
    def _calc_workflow_states(self):
        model_id = self.env['ir.model']._get_id(self._name) 
        state_ids= self.env['approval.config'].search([('model_id','=', model_id), ('active','=', True)])
        for record in self:
            res = [record._get_draft_state()]
            if record.id:
                eval_context = record._get_eval_context()
                for state_id in state_ids:
                    result = safe_eval(state_id.condition, eval_context)
                    if result:
                        res.append(state_id.state)
            if record.state_id:
                res.append(record._get_approved_state())
            record.workflow_states = json.dumps(res)
                    
    
    def _get_eval_context(self, user = None):
        user = user or self.env.user
        vals = self.env['ir.actions.actions']._get_eval_context()
        vals.update({
            'user' : user,
            'uid' : user.id,
            'self' : self,
            'record' : self,
            'object' : self,
            'env' : self.env,
            'Warning': Warning,
            'relativedelta' : relativedelta
            })
        return vals
            
    
    def _match_condition_user(self, filter_condition, user, delegation_roles_ids = False):
        if user.id == SUPERUSER_ID:
            return True
        res = safe_eval(filter_condition, self._get_eval_context(user))
        if res:
            return bool(res)
        if 'delegation' in self.env and delegation_roles_ids:
            user = user.with_context(delegation_roles_ids = delegation_roles_ids)
            for delegator in user.delegator_user_ids:
                res = safe_eval(filter_condition, self._get_eval_context(user = delegator))
                if res:
                    return bool(res)
        return False         
    
    @api.model
    def _before_approval_states_custom(self):
        model_id = self.env['ir.model']._get_id(self._name) 
        states=self.env['approval.settings.state'].search([('settings_id.model_id','=', model_id), ('type','=','before'), ('active','=', True)])
        if states:
            return [(state.state, state.name) for state in states]        
        return False
    
    @api.model
    def _before_approval_states(self):
        return self._before_approval_states_custom() or [('draft', _('Draft'))]
    
    @api.model
    def _after_approval_states_custom(self):
        model_id = self.env['ir.model']._get_id(self._name) 
        states=self.env['approval.settings.state'].search([('settings_id.model_id','=', model_id), ('type','=','after'), ('active','=', True)])
        if states:
            return [(state.state, state.name) for state in states]                
        return False
    
    @api.model
    def _after_approval_states(self):       
        return self._after_approval_states_custom() or [('approved', _('Approved')), ('rejected', _('Rejected'))]
    
    
    @api.model
    def _before_approval_states_values(self):
        return [state[0] for state in self._before_approval_states()]
    
    @api.model
    def _after_approval_states_values(self):
        return [state[0] for state in self._after_approval_states()]
                    
    @api.model
    def _approval_states(self):
        model_id = self.env['ir.model']._get_id(self._name)        
        records = self.env['approval.config'].search([('model_id', '=', model_id), ('active','=', True)])
        return [(record.state, record.name) for record in records]
    
    
    def _get_draft_state(self):
        values = self._before_approval_states_values()
        return values and values[0]
    
    
    def _get_reject_state(self):
        model_id = self.env['ir.model']._get_id(self._name) 
        state=self.env['approval.settings.state'].search([('settings_id.model_id','=', model_id), ('type','=','after'), ('active','=', True), ('reject_state','=', True)], limit =1)
        return state.state or 'rejected'
    
    
    def _get_approved_state(self):
        return self._after_approval_states_values()[0]
            
    @api.depends('state')
    def _calc_state_id(self):
        model_id = self.env['ir.model']._get_id(self._name)
        for record in self:
            record.state_id = self.env['approval.config'].search([('model_id','=', model_id), ('state','=', record.state)], limit = 1).id                    
    
    @api.depends('state')
    def _calc_state_name(self):
        vals = dict(self._fields['state']._description_selection(self.env))
        for record in self:
            record.state_name = vals.get(record.state)
    
    @api.model  
    def _search_state_id(self, operator, value):        
        if value is True:
            assert operator in ('=', '!=')
            value = False
            operator = operator=='=' and '!=' or '='            
        model_id = self.env['ir.model']._get_id(self._name)
        records = self.env['approval.config'].search([('id', operator, value), ('model_id', '=', model_id)])
        return [('state','in', records.mapped('state'))]
    
    @api.depends('state', 'state_id')
    def _calc_waiting_approval(self):
        for record in self:
            record.waiting_approval = bool(record.state_id)
            
    def _search_waiting_approval(self, operator, value):
        return [('state_id', operator, value)]
    
    @api.depends('state', 'state_id')
    def _calc_approval_user_ids(self):
        model_id = self.env['ir.model']._get_id(self._name)
        for record in self:
            state_id = record.state_id
            if state_id:                
                
                approval_forward_id = self.env['approval.forward'].search([('model_id', '=', model_id), ('record_id', '=', record.id), ('state_id', '=', state_id.id), ('active', '=', True)])                
                if approval_forward_id:
                    user_ids = approval_forward_id.user_id
                    
                else:
                    user_ids = state_id.mapped('group_ids.users')
                    if 'delegation' in self.env:
                        user_ids |= user_ids.with_context(delegation_roles_ids = state_id.group_ids.ids).mapped('delegated_user_ids')
                    if state_id.filter_condition:
                        user_ids = user_ids.filtered(lambda user_id : record._match_condition_user(state_id.filter_condition, user_id, state_id.group_ids.ids))                                
                    for user in list(user_ids):
                        env2 = self.env(user = user.id, context = {}, su = False)
                        model = env2[self._name]
                        try:
                            model.check_access_rights('read')
                            model.browse(record.id).check_access_rule('read')
                        except AccessError:
                            user_ids -=user
                            continue                
                
                user_ids += user_ids.browse(SUPERUSER_ID)
                
                record.approval_user_ids = user_ids
                record.user_can_approve = bool(user_ids & self.env.user)
                user_ids = user_ids.filtered(lambda user : user != self.env.ref('base.user_root') and user != self.env.ref('base.user_admin'))
                record.approval_user2_ids = user_ids
                record.approval_partner_ids = ','.join(map(str,user_ids.mapped('partner_id.id')))
            else:
                record.approval_user_ids = False
                record.approval_user2_ids = False
                record.approval_partner_ids = False
                record.user_can_approve = False
                
    
    @api.depends('approval_user_ids')            
    def _calc_approval_emp_emails(self):
        if 'hr.employee' in self.env:
            email_field = 'approval_user_ids.employee_ids.work_email'
        else:
            email_field = 'approval_user_ids.email'
        for record in self:
            record.approval_emp_emails = ','.join(filter(None,set(record.mapped(email_field))))
                
    def _search_approval_user_ids(self, operator, value):
        user_ids = self.env['res.users'].search([('id', operator, value)])
        model_id = self.env['ir.model']._get_id(self._name)
        state_ids = self.env['approval.config'].search([('model_id','=', model_id), ('group_ids','in', user_ids.mapped('wkf_groups_ids.id'))])
        state_ids += self.env['approval.forward'].search([('model_id','=', model_id), ('user_id','in', user_ids.ids), ('active', '=', True)]).mapped('state_id')
        ids = []
        for state_id in state_ids:
            records= self.search([('state', '=', state_id.state)])
            for record in records:
                if record.approval_user_ids & user_ids:
                    ids.append(record.id)                            
        return [('id', 'in', ids)]
            
    @api.depends('state','state_id', 'user_can_approve')
    def _calc_button_enabled(self):
        for record in self:
            need_approval = bool(record.state_id or record.state in self._before_approval_states_values())
            user_can_approve = record.state in self._before_approval_states_values() or record.user_can_approve
            record.button_approve_enabled = need_approval and user_can_approve
            record.button_forward_enabled = record.user_can_approve and record.state_id.allow_forward
            record.button_return_enabled = record.user_can_approve and record.state_id.allow_return
            record.button_transfer_enabled = record.user_can_approve and record.state_id.allow_transfer
            
    @api.depends('state')
    def _calc_button_draft_enabled(self):
        for record in self:
            record.button_draft_enabled = record.state != record._get_draft_state()
            
    
    def _on_approve(self):
        "on user approve, approve state"
        self.state = self._get_approved_state()
    
    
    def _on_script_custom(self, name, **kwargs):
        model_id = self.env['ir.model']._get_id(self._name)
        script=self.env['approval.settings'].search([('model_id', '=', model_id)])[name]
        if script:
            eval_context = self._get_eval_context()
            eval_context.update(kwargs)
            safe_eval(script, eval_context, mode='exec')
            return True
        return False
        
        
    
    def _on_submit(self):
        "on user submit, first approval state"
        pass        
        
    
    
    def _on_approval(self, old_state, new_state):
        "on user approve, next state"
        pass
    
    
    def _on_reject(self):
        "on user reject"
        pass    
    
    
    def _schedule_approval_activity(self, users = None):
        if users is None:
            users = self.approval_user2_ids                
        if not self.state_id.schedule_activity:
            return
        if self.state_id.schedule_activity_field_id:
            date_deadline = self[self.state_id.schedule_activity_field_id.name] or fields.Date.context_today(self)
        else:
            date_deadline = fields.Date.context_today(self)
        date_deadline += timedelta(days = self.state_id.schedule_activity_days)
        for user in users:
            self.env['mail.activity'].sudo().with_context(disable_message_subscribe = True, mail_activity_quick_update = True).create({
                'user_id' : user.id,
                'res_id' : self.id,
                'res_model_id' : self.env['ir.model']._get_id(self._name),
                'activity_type_id' : self.env.ref('oi_workflow.activity_type_approval').id,
                'summary' : _('Waiting Approval'),
                'date_deadline' : date_deadline,
                'automated' : True
                })
            
    
    def _remove_approval_activity(self, action = None, reason = None, old_state_id = None, user_id = None, forward_user = None):
        model_id = self.env['ir.model']._get_id(self._name)
        self.env['approval.forward'].sudo().search([('model_id', '=', model_id), ('record_id', 'in', self.ids), ('active', '=', True)]).write({'active' : False})
        if action=='approved' and reason is None:
            reason = self._context.get('reject_reason')
        for record in self:            
            domain = [('res_model','=', record._name), 
                     ('res_id','=', record.id),
                     ('activity_type_id', '=', self.env.ref('oi_workflow.activity_type_approval').id)
                     ]
            if user_id:
                domain.append(('user_id', '=', user_id))
            activity_ids = self.env['mail.activity'].sudo().search(domain)                
            activity_ids.unlink()    
            post_msg = (action == 'approved' and old_state_id.post_approval_msg) or (action == 'rejected' and old_state_id.post_reject_msg) \
                or action == 'return' or action == 'forward' or action == 'transfer' 
            if action and self._isinstance('mail.thread') and post_msg:
                view_xmlid = 'oi_workflow.approval_record_%s' % action
                values = {
                    'record' : record,
                    'user' : self.env.user,
                    'reason' : reason,
                    'forward_user' : forward_user
                    }
                record.message_post_with_view(view_xmlid, 
                                            values = values, 
                                            subtype_id=self.env.ref('mail.mt_activities').id, 
                                            mail_activity_type_id = self.env.ref('oi_workflow.activity_type_approval').id)
            
       
    def _update_approval_activity(self):
        domain = [('res_model','=', self._name), 
                 ('res_id','=', self.id),
                 ('activity_type_id', '=', self.env.ref('oi_workflow.activity_type_approval').id)
                 ]        
        activity_ids = self.env['mail.activity'].search(domain)
        activity_to_delete = self.env['mail.activity']
        
        for activity_id in activity_ids:
            if activity_id.user_id not in self.approval_user2_ids or not self.state_id.schedule_activity:
                activity_to_delete += activity_id
                
        self._schedule_approval_activity (users = self.approval_user2_ids - activity_ids.mapped('user_id'))                                
        activity_to_delete.unlink()

        
    def action_approve(self):
        self = self.filtered('button_approve_enabled')
        self._action_approve()

        for record in self:
            if record.state_id.auto_approve and record.button_approve_enabled:
                record.action_approve()
    
    
    def _action_approve(self):        
        for record in self:            
            old_state = record.state
            old_state_id = record.state_id
            if not old_state_id:
                record._on_script_custom('on_submit') or record._on_submit()
            nextstate =record.state_id._get_next(record)
            if old_state_id.on_script:
                safe_eval(old_state_id.on_script, record._get_eval_context(), mode='exec')
            if not nextstate:
                record._on_script_custom('on_approve') or record._on_approve()
                record._on_script_custom('on_approval', old_state=old_state, new_state=record.state) or record._on_approval(old_state, record.state)                
            else:
                if record.state != nextstate.state:
                    record.state = nextstate.state   
                    record._on_script_custom('on_approval', old_state=old_state, new_state=record.state) or record._on_approval(old_state, record.state)             
            if old_state != record.state:                
                record._remove_approval_activity('approved', old_state_id = old_state_id)
                if not self._context.get('approval_no_mail'):
                    for template_id in nextstate.template_ids:
                        template_id.with_context(active_model = self._name).send_mail(record.id)
                    if nextstate.auto_subscribe_users:
                        record.message_subscribe(partner_ids=record.approval_user2_ids.mapped('partner_id.id'))
                    if nextstate.schedule_activity:
                        record._schedule_approval_activity() 
                if nextstate.before_script:
                    safe_eval(nextstate.before_script, record._get_eval_context(), mode='exec')
                if old_state_id.after_script:
                    safe_eval(old_state_id.after_script, record._get_eval_context(), mode='exec')
                      
    
    def action_reject(self, reason = None):
        self = self.filtered('button_approve_enabled')
        self._action_reject(reason = reason)
                                            
    
    def _action_reject(self, reason = None):
        self = self.filtered('button_approve_enabled')
        for record in self:
            record._remove_approval_activity('rejected', reason, old_state_id= record.state_id)            
            reject_script=record.state_id.reject_script
            state = ''
            old_state = record.state
            if reject_script:
                localdict = record._get_eval_context()
                localdict['reason'] = reason
                safe_eval(reject_script, localdict, mode='exec', nocopy=True)
                state = localdict.get('state')
            reject_template_ids = record.state_id.reject_template_ids
            record.with_context(reject_reason = reason).write({'state' : state or self._get_reject_state()})
            for template in reject_template_ids:
                template.with_context(active_model = self._name).send_mail(record.id)
            record._on_script_custom('on_reject', old_state = old_state) or record._on_reject()  
        
    
    def action_reject_wizard(self):
        context = dict(self._context)
        context.update({
            'active_model' : self._name,
            'active_ids' : self.ids,
            'active_id' : self.id
            })
        model_id = self.env['ir.model']._get(self._name)
        return {
            'type' : 'ir.actions.act_window',
            'name' : _('Reject %s : %s') % (model_id.name,self.display_name),
            'res_model' : 'approval.reject.wizard',
            'target' : 'new',
            'view_mode' : 'form',
            'view_type' : 'form',
            'context' : context
            }   
                             
    def action_approve_wizard(self):
        context = dict(self._context)
        context.update({
            'active_model' : self._name,
            'active_ids' : self.ids,
            'active_id' : self.id
            })
        model_id = self.env['ir.model']._get(self._name)
        return {
            'type' : 'ir.actions.act_window',
            'name' : _('Approve %s : %s') % (model_id.name,self.display_name),
            'res_model' : 'approval.approve.wizard',
            'target' : 'new',
            'view_mode' : 'form',
            'view_type' : 'form',
            'context' : context
            }   
        
    def action_draft(self):
        records = self.filtered('button_draft_enabled')
        self._remove_approval_activity()
        records.write({
            'state': self._get_draft_state()
        })        
        
    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def create(self, vals_list): 
        records= super(ApprovalRecord, self).create(vals_list)
        for record in records:
            record._after_save()
        return records
    
    
    def write(self, vals):
        reject_reason = self._context.get('reject_reason')
        if 'state' in vals:
            vals['last_state_update'] = fields.Datetime.now()
        states = self._read_field('state')
        res=super(ApprovalRecord, self).write(vals)
        self._after_save(vals, states, reject_reason)
        return res
    
    
    def _after_save(self, vals = None, old_states = {}, reject_reason = False):        
        if vals is None or 'state' in vals:
            model_id = self.env['ir.model']._get_id(self._name)
            for record in self:
                if record.state != old_states.get(record.id):
                    self.env['approval.log'].sudo().create({
                        'record_id' : record.id,
                        'user_id' : self.env.user.id,
                        'date' : fields.Datetime.now(),
                        'state' : record.state,
                        'model_id' : model_id,
                        'description' : reject_reason
                        })
                               
    
    def unlink(self):
        for record in self:
            if record.state != self._get_draft_state():
                raise ValidationError(_('You can delete in %s status only') % self._get_draft_state())        
        model_id = self.env['ir.model']._get_id(self._name)
        self.env['approval.log'].sudo().search([('model_id','=', model_id), ('record_id', 'in', self.ids)]).unlink()
        return super(ApprovalRecord, self).unlink()
                    
    @api.model
    def _create_approval_settings(self):
        model_id = self.env['ir.model']._get_id(self._name)
        record = self.env['approval.settings'].search([('model_id','=', model_id)])
        if model_id and not record:
            record = self.env['approval.settings'].create({
                'model_id' : model_id,                
            })
        if record:
            ref = record.with_context(is_approval_setting = True)._create_external_id()
            xmlid, _, _ = self.env['ir.model.data'].xmlid_lookup(ref)
            xmlid =  self.env['ir.model.data'].browse(xmlid)
            if xmlid.module == 'oi_workflow':
                xmlid.module = '_workflow'
            if not xmlid.noupdate and xmlid.module == '_workflow':
                xmlid.noupdate = True                
             
    def init(self):
        super(ApprovalRecord, self).init()
        if not self._abstract:
            self._create_approval_settings()
                
                
    def action_forward(self):
        context = dict(self._context)
        context.update({
            'active_model' : self._name,
            'active_ids' : self.ids,
            'active_id' : self.id
            })
        if self._context.get('forward_to_group'):
            context.update({
            'forward_to_group' : self._context.get('forward_to_group'),
            })
        model_id = self.env['ir.model']._get(self._name)
        return {
            'type' : 'ir.actions.act_window',
            'name' : _('Forward %s : %s') % (model_id.name,self.display_name),
            'res_model' : 'approval.forward.wizard',
            'target' : 'new',
            'view_mode' : 'form',
            'view_type' : 'form',
            'context' : context
            }               
                
                
    def action_return(self):
        context = dict(self._context)
        context.update({
            'active_model' : self._name,
            'active_ids' : self.ids,
            'active_id' : self.id
            })
        if self._context.get('fixed_return_state'):
            context.update({
            'default_state' : self._context.get('fixed_return_state'),
            })
        model_id = self.env['ir.model']._get(self._name)
        return {
            'type' : 'ir.actions.act_window',
            'name' : _('Return %s : %s') % (model_id.name,self.display_name),
            'res_model' : 'approval.return.wizard',
            'target' : 'new',
            'view_mode' : 'form',
            'view_type' : 'form',
            'context' : context
            }  
        
    def action_transfer(self):
        context = dict(self._context)
        context.update({
            'active_model' : self._name,
            'active_ids' : self.ids,
            'active_id' : self.id
            })
        if self._context.get('fixed_transfer_state'):
            context.update({
            'default_state' : self._context.get('fixed_transfer_state'),
            })
        model_id = self.env['ir.model']._get(self._name)
        return {
            'type' : 'ir.actions.act_window',
            'name' : _('Transfer %s : %s') % (model_id.name,self.display_name),
            'res_model' : 'approval.transfer.wizard',
            'target' : 'new',
            'view_mode' : 'form',
            'view_type' : 'form',
            'context' : context
            }         
                                
    def _action_forward(self, user_id, reason):        
        self = self.filtered('button_approve_enabled')
        model_id = self.env['ir.model']._get_id(self._name)
        context = dict(self._context)
        if self._context.get('fixed_group'):
            context.update({
            'fixed_group' : self._context.get('fixed_group'),
            })
        for record in self:
            record._remove_approval_activity(action='forward', reason = reason, forward_user = user_id)            
            self.env['approval.forward'].sudo().create({
                'model_id' : model_id,
                'record_id' : record.id,
                'state_id' : record.state_id.id,
                'user_id' : user_id.id,
                'forwarder_user_id' : self.env.user.id,
                'reason' : reason
                })            
            
        self.invalidate_cache()
        
        for record in self:
            record._schedule_approval_activity()
            record._on_script_custom('on_forward', user_id = user_id, reason = reason) or record._on_forward(user_id = user_id, reason = reason)
            
            if not self._context.get('approval_no_mail'):
                for template_id in record.state_id.template_ids:
                    template_id.with_context(active_model = self._name, reason = reason, forwarder_user = self.env.user).send_mail(record.id)

            
    def _action_return(self, state, reason):        
        if self._context.get('return_check_approval', True):
            self = self.filtered('button_approve_enabled')        
        old_states = {}
        for record in self:
            old_states[record] = record.state
            record._remove_approval_activity(action='return', reason = reason)   
            record.with_context(reject_reason = reason).write({'state' : state})
            
        self.invalidate_cache()
        
        for record in self:
            record._schedule_approval_activity()
            record._on_script_custom('on_return', new_state = state, old_state =old_states[record], reason = reason) or record._on_return(new_state = state, old_state =old_states[record], reason = reason)
            
    def _action_transfer(self, state, reason):        
        self = self.filtered('button_approve_enabled')        
        old_states = {}
        for record in self:
            old_states[record] = record.state
            record._remove_approval_activity(action='transfer', reason = reason)            
            record.with_context(reject_reason = reason).write({'state' : state})
            
        self.invalidate_cache()
        
        for record in self:
            record._schedule_approval_activity()
            record._on_script_custom('on_transfer', new_state = state, old_state =old_states[record], reason = reason) or record._on_transfer(new_state = state, old_state =old_states[record], reason = reason)                        
    
    def _on_forward(self, user_id = None, reason = None):
        pass
    
    def _on_return(self, new_state = None, old_state = None, reason = None):
        pass
    
    def _on_transfer(self, new_state = None, old_state = None, reason = None):
        pass
    
    def _expand_states(self, states, domain, order):
        values = self._fields['state'].get_values(self.env)
        if self._context.get('expand_states_full'):
            return values
        return sorted(states, key = lambda state: values.index(state))     
                