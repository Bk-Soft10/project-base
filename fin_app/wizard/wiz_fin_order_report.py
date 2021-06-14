from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning ,UserError, ValidationError
from datetime import datetime, timedelta
import time
from dateutil import relativedelta
import odoo.addons.decimal_precision as dp
from odoo.tools.float_utils import float_round, float_compare

#################################################################################################################
#################################################################################################################
class wiz_order_report(models.TransientModel):
	_name = 'wiz.fin.order.report'
	date_from = fields.Date('F-Date', default=time.strftime('%Y-%m-01'), required=True)
	date_to = fields.Date('T-Date', default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10], required=True)
	partner_ids = fields.Many2many('res.partner', 'rel_partner_order_wiz', 'wiz_id', 'order_id', string='Partner')
	report_type = fields.Selection([
		('sale', 'Sale Order'),
		('purchase', 'Purchase Order'),
		('out_invoice', 'Sale Invoices'),
		('in_invoice', 'Purchase Invoices'),
		('inbound', 'Customer Payments'),
		('outbound', 'Vendor Payments'),
		('out_refund', 'Credit Notes'),
		('in_refund', 'Refund'),
		],string='Type')
	state = fields.Selection([('all', 'All'), ('confirm', 'Confirmed')], string='State', default='all')

	def print_report(self):
		self.ensure_one()
		if self.report_type and self.date_from and self.date_to:
			data = {}
			data = self.read(['report_type', 'partner_ids', 'date_from', 'date_to', 'state'])[0]
			return self.env.ref('fin_app.action_fin_report_order_app').report_action(self, data=data)
