from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning ,UserError, ValidationError
from datetime import datetime
import odoo.addons.decimal_precision as dp
from odoo.tools.float_utils import float_round, float_compare

#################################################################################################################
#################################################################################################################

#################################################################################################################
# Create the fin.user model
#################################################################################################################

class fin_user(models.Model):
	_name = 'fin.user'
	_description = "User Fin App"
	name = fields.Char(string="Name", required=True)
	email = fields.Char(string='E-Mail', required=True)
	passw = fields.Char(string='Password', required=True)
	user_id = fields.Many2one('res.users', string='User ID', readonly=True)
	group_id = fields.Many2one('res.groups', string='Access Group', domain="[('category_id.name','=','Fin App')]")
	created = fields.Boolean(string='Created', readonly=True)

	def add_user(self):
		self.ensure_one()
		if self.name and self.email and self.passw and self.group_id:
			list_group = []
			list_group.append(self.group_id.id)
			if not self.user_id:
				self.user_id = self.user_id.create({
					'name': self.name,
					'login': self.email,
					'password': self.passw,
					'groups_id': [(6, 0, list_group)]
				})
				self.created = True
			else:
				self.user_id.write({
					'name': self.name,
					'login': self.email,
					'password': self.passw,
					'groups_id': [(6, 0, list_group)]})
		return self.user_id