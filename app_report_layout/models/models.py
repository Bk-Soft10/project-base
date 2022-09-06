from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, UserError, ValidationError
##################################################################################################################################################3
####################################################################################################################################################3

class ResCompany(models.Model):
    _inherit = 'res.company'

    report_header_img = fields.Binary('Report header')
    report_footer_img = fields.Binary('Report footer')