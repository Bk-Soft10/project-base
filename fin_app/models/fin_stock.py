from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning ,UserError, ValidationError
from datetime import datetime
import odoo.addons.decimal_precision as dp
from odoo.tools.float_utils import float_round, float_compare

#################################################################################################################
#################################################################################################################

#################################################################################################################
# inherit the stock.move model
#################################################################################################################

class stock_move(models.Model):
	_inherit = "stock.move"

	product_uom_qty = fields.Integer('Initial Demand', digits='Product Unit of Measure', default=0, required=True, states={'done': [('readonly', True)]},
									 help="This is the quantity of products from an inventory "
									 "point of view. For moves in the state 'done', this is the "
									 "quantity of products that were actually moved. For other "
									 "moves, this is the quantity of product that is planned to "
									 "be moved. Lowering this quantity does not generate a "
									 "backorder. Changing this quantity on assigned moves affects "
									 "the product reservation, and should be done with care.")

#################################################################################################################
# inherit the stock.move.line model
#################################################################################################################

class stock_move_line(models.Model):
	_inherit = "stock.move.line"

	# product_uom_qty = fields.Integer('Reserved', required=True)
	qty_done = fields.Integer('Done')