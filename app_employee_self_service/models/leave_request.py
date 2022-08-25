from odoo import api, fields, models, _
from datetime import datetime, date, timedelta, time
from pytz import timezone, UTC
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
from odoo.exceptions import ValidationError

##################################################################################################################################################
###################################################################################################################################################

class LeaveRequest(models.Model):
    _name = 'req.leave_request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherits = {'req.self_service': 'req_id'}
    _description = "Leave Requests"

    req_id = fields.Many2one('req.self_service', string='Request', copy=False, auto_join=True, index=True, ondelete="cascade", required=True)
    source_model = fields.Char(default='req.leave_request', related='req_id.source_model', store=True, readonly=False)

    leave_type_id = fields.Many2one('hr.leave.type', string='Leave Type', required=True, readonly=False, domain=[('valid', '=', True)])
    description = fields.Char('Description', copy=False)
    date_from = fields.Date(string='From', copy=False)
    date_to = fields.Date(string='To', copy=False)
    balance = fields.Float(string='Annual Leave Current Balance', copy=False)
    new_balance = fields.Float(string='New Balance', copy=False)
    num_days = fields.Float(string='Number of Days', copy=False)


    @api.constrains('date_from', 'date_to')
    def _check_date(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_from > rec.date_to:
                raise ValidationError(_('Re-check Dates From/TO'))

    def _get_number_of_days(self, date_from, date_to, employee_id):
        """ Returns a float equals to the timedelta between two dates given as string."""
        if employee_id:
            employee = self.env['hr.employee'].browse(employee_id)
            # We force the company in the domain as we are more than likely in a compute_sudo
            domain = [('company_id', 'in', self.env.company.ids + self.env.context.get('allowed_company_ids', []))]
            return employee._get_work_days_data_batch(date_from, date_to, domain=domain)[employee.id]

        today_hours = self.env.company.resource_calendar_id.get_work_hours_count(
            datetime.combine(date_from.date(), time.min),
            datetime.combine(date_from.date(), time.max),
            False)

        hours = self.env.company.resource_calendar_id.get_work_hours_count(date_from, date_to)

        return {'days': hours / (today_hours or HOURS_PER_DAY), 'hours': hours}

    @api.onchange('date_from', 'date_to', 'employee_id')
    def _onchange_leave_dates(self):
        for rec in self:
            if rec.date_from and rec.date_to:
                rec.num_days = rec._get_number_of_days(rec.date_from, rec.date_to, rec.employee_id.id)['days']
            else:
                rec.num_days = 0

    @api.onchange('num_days', 'balance')
    def _set_new_balance(self):
        for rec in self:
            if rec.balance and rec.num_days:
                rec.new_balance = rec.balance - rec.num_days

    @api.constrains('new_balance')
    def _check_new_balance(self):
        for rec in self:
            if rec.new_balance < 0:
                raise ValidationError(_('Please Re-check Iban Number'))

    def unlink(self):
        for rec in self:
            if rec.req_id:
                rec.req_id.unlink()
        return super(LeaveRequest, self).unlink()

    @api.model
    def create(self, vals):
        res = super(LeaveRequest, self).create(vals)
        if res and res.req_id:
            res.req_id.source_id = res.id
        return res

    def write(self, vals):
        res = super(LeaveRequest, self).write(vals)
        for rec in self:
            if rec and rec.req_id:
                rec.req_id.source_id = rec.id
        return res