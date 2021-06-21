from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning ,UserError, ValidationError
from datetime import datetime
import odoo.addons.decimal_precision as dp
from odoo.tools.float_utils import float_round, float_compare

#################################################################################################################
#################################################################################################################

#################################################################################################################
# inherit the sale.order model
#################################################################################################################

class sale_order(models.Model):
	_inherit = 'sale.order'

	def action_confirm(self):
		super(sale_order, self).action_confirm()
		auto_pick_so = self.env['ir.config_parameter'].sudo().get_param('fin_app.auto_pick_so')
		if auto_pick_so:
			# for rec_pick in self.mapped('picking_ids'):
			# 	rec_pick.sudo().action_confirm()
			# 	rec_pick.sudo().action_assign()
			# 	rec_pick.sudo().button_validate()
				# ## comment lines ###
				# wiz = self.env['stock.immediate.transfer']
				# wiz_id = wiz.create({'pick_ids':[(4,rec_pick.id)]})
				# wiz_id.process()
			for rec_line in self.mapped('order_line'):
				rec_line.product_id.sudo().write({'invoice_policy': 'order'})
			wiz = self.env['sale.advance.payment.inv']
			wiz_id = wiz.with_context(active_ids=self.ids).create({'advance_payment_method': 'delivered'})
			# return wiz_id.with_context(open_invoices=True).create_invoices()
			return wiz_id.create_invoices()

#################################################################################################################
# inherit the sale.order.line model
#################################################################################################################

class sale_order_line(models.Model):
	_inherit = 'sale.order.line'

	product_uom_qty = fields.Integer(string='Quantity', required=True, default=1)
	# categ_id = fields.Many2one('product.category', string='Product Category')
	# product_model = fields.Many2one('fin.product.model', string='Product Model')
	#
	# @api.onchange('categ_id', 'product_model')
	# def _get_product_domain_fin(self):
	# 	for rec in self:
	# 		product_recs = False
	# 		if rec.categ_id:
	# 			domain_lst = [('categ_id', '=', rec.categ_id.id)]
	# 			product_recs = self.env['product.product'].search(domain_lst) or False
	# 			if rec.product_model and product_recs:
	# 				product_recs = product_recs.filtered(lambda pro: rec.product_model.id in pro.product_model.ids) or False
	# 			if product_recs:
	# 				return {'domain': {'product_id': [('id', 'in', product_recs.ids)]}}
	# 		return {'domain': {'product_id': [('id', '=', 0)]}}