from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning ,UserError, ValidationError
from datetime import datetime
import odoo.addons.decimal_precision as dp
from odoo.tools.float_utils import float_round, float_compare

#################################################################################################################
#################################################################################################################
class wiz_product_updatee(models.TransientModel):
	_name = 'wiz.product.update.price'
	price_add = fields.Float('Price Added')
	has_all = fields.Boolean('All Product')
	product_ids = fields.Many2many('product.template', 'product_wiz_rel', 'wiz_id', 'pro_id', string='Product', store=True)
	type_inv = fields.Selection([('percentage', 'Percentage'), ('fix', 'Fix Price')], string='Change Type', readonly=False, default='fix')

	def save_update(self):
		self.ensure_one()
		if self.product_ids:
			pro_ids = self.product_ids
		else:
			pro_ids = self.env['product.template'].search([])
		if self.type_inv == 'percentage':
			for pro in pro_ids:
				pro.lst_price = (pro.lst_price * self.price_add/100) + pro.lst_price
		elif self.type_inv == 'fix':
			for pro in pro_ids:
				pro.lst_price = self.price_add + pro.lst_price
		return {'type': 'ir.actions.act_window_close'}
