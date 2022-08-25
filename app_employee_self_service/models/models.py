from odoo import api, fields, models, _
from datetime import datetime

##################################################################################################################################################
###################################################################################################################################################

class AppRequestService(models.Model):
    _name = 'req.self_service'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Self-Service Requests"

    def _default_employee(self):
        return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    code = fields.Char('Code', copy=False, default='/')
    source_model = fields.Char(string='Source Model', copy=False)
    source_id = fields.Char(string='Source ID', copy=False)
    justification = fields.Text('Justification', copy=False)
    employee_id = fields.Many2one('hr.employee', string='Employee', copy=False, default=_default_employee, required=True)
    department_id = fields.Many2one('hr.department', string='Department', copy=False)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', copy=False)
    user_id = fields.Many2one('res.users', string='Requested by', copy=False, required=True, default=lambda self: self.env.user)
    supportive_documents = fields.Many2many('ir.attachment', string='Supportive Documents', copy=False)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    active = fields.Boolean(string='Active', default=True, copy=False)
    request_date = fields.Date('Request Date', default=fields.Date.today, copy=False, required=True)
    state = fields.Selection([('draft', 'Draft'), ('PM Approval', 'PM Approval'), ('HRO Approval', 'HRO Approval'), ('done', 'Done'), ('cancel', 'Canceled'), ('reject', 'Rejected')], string='Status', copy=False,
                                     default='draft')

    @api.model
    def create(self, vals):
        vals['code'] = self.env['ir.sequence'].get('req.self_service')
        res = super(AppRequestService, self).create(vals)
        return res

    def set_draft(self):
        self.ensure_one()
        self.state = 'draft'

    def set_pm(self):
        self.ensure_one()
        self.state = 'PM Approval'
        email_templ = self.env.ref('app_employee_self_service.email_self_service_wait_approve', raise_if_not_found=False) or False
        partner_ids = [self.env.user.partner_id]
        if partner_ids and email_templ:
            self.send_email(self.id, email_templ, partner_ids)

    def set_hro(self):
        self.ensure_one()
        self.state = 'HRO Approval'
        email_templ = self.env.ref('app_employee_self_service.email_self_service_wait_approve', raise_if_not_found=False) or False
        partner_ids = [self.env.user.partner_id]
        if partner_ids and email_templ:
            self.send_email(self.id, email_templ, partner_ids)

    def set_done(self):
        self.ensure_one()
        self.state = 'done'
        email_templ = self.env.ref('app_employee_self_service.email_self_service_approved', raise_if_not_found=False) or False
        partner_ids = [self.env.user.partner_id]
        if partner_ids and email_templ:
            self.send_email(self.id, email_templ, partner_ids)

    def set_cancel(self):
        self.ensure_one()
        self.state = 'cancel'

    def set_reject(self):
        self.ensure_one()
        self.state = 'reject'
        email_templ = self.env.ref('app_employee_self_service.email_self_service_reject', raise_if_not_found=False) or False
        partner_ids = [self.env.user.partner_id]
        if partner_ids and email_templ:
            self.send_email(self.id, email_templ, partner_ids)

    @api.onchange('employee_id')
    def _change_employee_val(self):
        for rec in self:
            if rec.employee_id:
                rec.department_id = rec.employee_id.department_id.id if rec.employee_id.department_id else False
                rec.analytic_account_id = rec.employee_id.department_id.analytic_account_id.id if rec.employee_id.department_id and rec.employee_id.department_id.analytic_account_id else False

    def open_source_document(self):
        self.ensure_one()
        if self.source_id and self.source_model:
            record = self.env[str(self.source_model)].search([('id', '=', int(self.source_id))], limit=1)
            if record:
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': self.source_model,
                    'view_mode': 'form',
                    'res_id': self.source_id
                }
        elif not self.source_id and self.source_model:
            record = self.env[str(self.source_model)].search([('req_id', 'in', self.ids)], limit=1)
            if record:
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': self.source_model,
                    'view_mode': 'form',
                    'res_id': self.source_id
                }




    def prepare_base_url(self):
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        base_url += '/web#id=%d&view_type=form&model=%s' % (self.source_id or self.id, self.source_model or self._name)
        return base_url

    def send_email(self, res_id, email_template, partner_ids):
        for partner_id in partner_ids:
            if partner_id.email and email_template and res_id:
                try:
                    email_id = email_template.with_context(lang=partner_id.lang).send_mail(res_id)
                    email = self.env['mail.mail'].browse(email_id)
                    email.write({'email_to': partner_id.email})
                    email_send = email.send()
                except:
                    pass