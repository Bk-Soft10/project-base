from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

###########################################################################################################
###########################################################################################################

class ResCompany(models.Model):
    _inherit = 'res.company'

    sale_price_type = fields.Selection([
        ('percentage', 'Percentage'), ('fixed', 'Fixed')
    ], string='Sale Price Type', default='percentage')
    sale_profit_margin = fields.Float(string='Sale Profit Margin', default=5.0)

    @api.constrains('sale_price_type', 'sale_profit_margin')
    def _check_sale_profit_margin(self):
        for rec in self:
            price_type = rec.sale_price_type
            sale_margin = rec.sale_profit_margin
            if sale_margin < 0:
                raise ValidationError(_("Sale Profit Margin must be greater than 0."))
            if price_type == 'percentage' and sale_margin > 100:
                rec.sale_profit_margin = 5.0
                raise ValidationError(_("Sale Profit Margin must be between 0 and 100 when Sale Price Type is Percentage."))

###########################################################################################################
###########################################################################################################

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sale_price_type = fields.Selection(related='company_id.sale_price_type', string='Sale Price Type', readonly=False)
    sale_profit_margin = fields.Float(related='company_id.sale_profit_margin', string='Sale Profit Margin', readonly=False)
