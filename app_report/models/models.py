from odoo import models, fields, api, _

class ResUsers(models.Model):
    _inherit = 'res.users'

    name_partner = fields.Char('Partner Name', related='partner_id.name', store=True)