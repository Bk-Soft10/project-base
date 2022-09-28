from odoo import models, api, fields


class PosOrderSerach(models.Model):
    _inherit = 'pos.order'

    plate = fields.Char(string=' License Plate', relate='partner_id.license_plate')
    customer_phone = fields.Char(string='Phone', relate='partner_id.phone')



class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    license_plate = fields.Char(string=' License Plate')