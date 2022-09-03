
from odoo import api, fields, models, _

#########################################################################
#########################################################################
#########################################################################
######  Inh Picking  ##########
#########################################################################

class app_inh_picking(models.Model):
    _inherit = 'stock.picking'

    workshop_id = fields.Many2one('app.workshop', string='Work-Order', copy=False)
    spare_order_id = fields.Many2one('app.workshop.spare.order', string='Spare Order', copy=False)


#########################################################################
######  Inh invoice  ##########
#########################################################################

class app_inh_invoice(models.Model):
    _inherit = 'account.move'

    workshop_id = fields.Many2one('app.workshop', string='Work-Order', copy=False)

    def write(self, vals):
        res = super(app_inh_invoice, self).write(vals)
        for r in self:
            if r.workshop_id:
                r.workshop_id.get_mergin_account()
        return res


#########################################################################
######  Inh Payment  ##########
#########################################################################

class app_inh_payment(models.Model):
    _inherit = 'account.payment'
    workshop_id = fields.Many2one('app.workshop', string='Work-Order', copy=False)
    invoice_id = fields.Many2one('account.move', string='Work-Invoice', readonly=False, store=True, copy=False)

    def write(self, vals):
        res = super(app_inh_payment, self).write(vals)
        for r in self:
            if r.workshop_id:
                r.workshop_id.get_mergin_account()
        return res


#########################################################################
######  Inh users  ##########
#########################################################################

class app_inh_users(models.Model):
    _inherit = 'res.users'
    file_order = fields.Binary('Attachment', copy=False)
    sign_user = fields.Binary('Signature', copy=False)


#########################################################################
######  Inh partner  ##########
#########################################################################

class app_inh_partnerr(models.Model):
    _inherit = 'res.partner'
    workshop_ids = fields.One2many('app.workshop', 'partner_id', string='Workshop Order List')
    number_partner = fields.Char('Number Code')


#########################################################################
######  Inh product  ##########
#########################################################################

class app_system_pro_template_inh(models.Model):
    _inherit = 'product.template'

    stander_time = fields.Float(string='Stander Time')