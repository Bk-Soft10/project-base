from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning ,UserError, ValidationError
from datetime import datetime
import odoo.addons.decimal_precision as dp
from odoo.tools.float_utils import float_round, float_compare

#################################################################################################################
#################################################################################################################

#################################################################################################################
# inherit the account.move.line model
#################################################################################################################

class account_move_line(models.Model):
	_inherit = "account.move.line"

	quantity = fields.Integer(string='Quantity', default=1,
							  help="The optional quantity expressed by this line, eg: number of product sold. "
								   "The quantity is not a legal requirement but is very useful for some reports.")