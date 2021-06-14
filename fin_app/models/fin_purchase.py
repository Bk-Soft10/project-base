from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning ,UserError, ValidationError
from datetime import datetime
import odoo.addons.decimal_precision as dp
from odoo.tools.float_utils import float_round, float_compare

#################################################################################################################
#################################################################################################################

#################################################################################################################
# inherit the purchase.order model
#################################################################################################################

class purchase_order(models.Model):
	_inherit = "purchase.order"

	def button_confirm(self):
		super(purchase_order, self).button_confirm()
		auto_pick_po = self.env['ir.config_parameter'].sudo().get_param('fin_app.auto_pick_po')
		if auto_pick_po:
			for rec_pick in self.mapped('picking_ids'):
				rec_pick.sudo().action_confirm()
				rec_pick.sudo().action_assign()
				rec_pick.sudo().button_validate()
				wiz = self.env['stock.immediate.transfer']
				wiz_id = wiz.create({'pick_ids': [(4, rec_pick.id)]})
				wiz_id.process()
			# self.action_view_invoice()
			# for rec_inv in self.mapped('invoice_ids'):
			# 	rec_inv.action_invoice_open()
			return self.sudo().action_view_invoice()