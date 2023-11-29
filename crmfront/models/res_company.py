from odoo import fields, models, api

class Company(models.Model):
    _inherit = 'res.company'

    customer_ids = fields.Many2many(
        string="Customers",
        comodel_name = 'res.partner',
        relation ='customer_company_rel',
        column1='company_id',
        column2='partner_id',
    )
    