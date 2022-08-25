from odoo import api, fields, models, _
from datetime import datetime, date, timedelta, time
from pytz import timezone, UTC
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
from odoo.exceptions import ValidationError

##################################################################################################################################################
###################################################################################################################################################

class DeputationRequest(models.Model):
    _name = 'req.deputation_request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherits = {'req.self_service': 'req_id'}
    _description = "Business Trip Requests"

    req_id = fields.Many2one('req.self_service', string='Request', copy=False, auto_join=True, index=True, ondelete="cascade", required=True)
    source_model = fields.Char(default='req.deputation_request', related='req_id.source_model', store=True, readonly=False)

    dest_country_id = fields.Many2one('res.country', string='Destination Country', copy=False, required=True,
                                 default=lambda self: self.env.company.country_id)
    dest_city_id = fields.Many2one('res.country.state', string='Destination City', copy=False, required=True)
    purpose = fields.Text('Occasion/Purpose', copy=False)
    date_from = fields.Date(string='From', copy=False)
    date_to = fields.Date(string='To', copy=False)
    num_days = fields.Float(string='Number of Days', copy=False)
    purpose_trip = fields.Selection([('Work Stay', 'Work Stay'), ('Training/Education', 'Training/Education'), ('Other', 'Other')], string='Purpose of trip', copy=False,
                                        default='Other')
    payment_method = fields.Selection([('Direct Deposit', 'Direct Deposit'), ('Cash', 'Cash')], string='Method of Payment', copy=False)
    travel_ticket = fields.Selection([('Yes', 'Yes'), ('No', 'No')], string='Need Travel Tickets', copy=False,
                                        default='No')


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
    def _onchange_deputation_dates(self):
        for rec in self:
            if rec.date_from and rec.date_to:
                rec.num_days = rec._get_number_of_days(rec.date_from, rec.date_to, rec.employee_id.id)['days']
            else:
                rec.num_days = 0

    def unlink(self):
        for rec in self:
            if rec.req_id:
                rec.req_id.unlink()
        return super(DeputationRequest, self).unlink()

    @api.model
    def create(self, vals):
        res = super(DeputationRequest, self).create(vals)
        if res and res.req_id:
            res.req_id.source_id = res.id
        return res

    def write(self, vals):
        res = super(DeputationRequest, self).write(vals)
        for rec in self:
            if rec and rec.req_id:
                rec.req_id.source_id = rec.id
        return res