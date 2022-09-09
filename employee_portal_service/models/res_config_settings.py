
from odoo import fields, models, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    portal_id = fields.Many2one('portal.website', string='Website Portal')

##############################################################################################################
###########################################################################################################

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    portal_id = fields.Many2one('portal.website', string='Website Portal', related='company_id.portal_id',
                                store=True, readonly=False)
