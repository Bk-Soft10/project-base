from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import ValidationError

##################################################################################################################################################
###################################################################################################################################################

class Travellers(models.Model):
    _name = 'traveller.line'
    _description = "Travellers"

    name = fields.Char(string='Traveller Name', copy=False)
    relative_relation = fields.Selection([('Wife', 'Wife'), ('Children', 'Children'), ('Infants', 'Infants')], string='Relative Relation', copy=False)
    travel_id = fields.Many2one('req.travel_tickets', string='Travel Ticket', copy=False)

##################################################################################################################################################
###################################################################################################################################################

##################################################################################################################################################
###################################################################################################################################################

class TravelTickets(models.Model):
    _name = 'req.travel_tickets'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherits = {'req.self_service': 'req_id'}
    _description = "Travel Tickets"

    req_id = fields.Many2one('req.self_service', string='Request', copy=False, auto_join=True, index=True, ondelete="cascade", required=True)
    source_model = fields.Char(default='req.travel_tickets', related='req_id.source_model', store=True, readonly=False)

    purpose = fields.Selection([('Business Trip', 'Business Trip'), ('Personal Vacation', 'Personal Vacation')],
                               string='Purpose', copy=False)
    trip_type = fields.Selection([('One Way', 'One Way'), ('Round Trip', 'Round Trip')], string='Trip Type', copy=False,
                                 default='One Way')
    tickets_class = fields.Selection([('Guest', 'Guest'), ('Business', 'Business')], string='Tickets Class', copy=False,
                                     default='Guest')
    other_travellers = fields.Selection([('Yes', 'Yes'), ('No', 'No')], string='Other Travellers', copy=False,
                                        default='No')
    date_from = fields.Date(string='Date From', copy=False)
    date_to = fields.Date(string='Date To', copy=False)
    place_from = fields.Char(string='From', copy=False)
    place_to = fields.Char(string='To', copy=False)
    travellers_ids = fields.One2many('traveller.line', 'travel_id', string='Travellers', copy=False)


    @api.constrains('date_from', 'date_to')
    def _check_date(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_from > rec.date_to:
                raise ValidationError(_('Re-check Dates From/TO'))

    def unlink(self):
        for rec in self:
            if rec.req_id:
                rec.req_id.unlink()
        return super(TravelTickets, self).unlink()

    @api.model
    def create(self, vals):
        res = super(TravelTickets, self).create(vals)
        if res and res.req_id:
            res.req_id.source_id = res.id
        return res

    def write(self, vals):
        res = super(TravelTickets, self).write(vals)
        for rec in self:
            if rec and rec.req_id:
                rec.req_id.source_id = rec.id
        return res