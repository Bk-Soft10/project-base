from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning ,UserError, ValidationError
from datetime import datetime
import odoo.addons.decimal_precision as dp
from odoo.tools.float_utils import float_round, float_compare

#################################################################################################################
#################################################################################################################

#################################################################################################################
# Create the fin.product.model model
#################################################################################################################

class fin_product_model(models.Model):
	_name = 'fin.product.model'
	_description = "Product Model Fin"

	name = fields.Char(string="Name", required=True, translate=True, unique=True)

#################################################################################################################
# inherit the product.template model
#################################################################################################################

class ProductTemplate(models.Model):
	_inherit = 'product.template'

	product_model = fields.Many2many('fin.product.model', string='Product Model')

#################################################################################################################
# inherit the product.product model
#################################################################################################################

# class ProductProduct(models.Model):
# 	_inherit = 'product.product'
#
# 	product_model = fields.Many2many('fin.product.model', string='Product Model')

#################################################################################################################
# inherit the product.category model
#################################################################################################################
#
# class ProductcCategory(models.Model):
# 	_inherit = 'product.category'
#
# 	product_model = fields.Many2many('fin.product.model', string='Product Model')