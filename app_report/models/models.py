from odoo import models, fields, api, _

class ResUsers(models.Model):
    _inherit = 'res.users'

    name_partner = fields.Char('Partner Name', related='partner_id.name', store=True)

####################################################################################################################################
#####################################################################################################################################

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    paid_total = fields.Float('Paid Total', store=True, compute='_get_paid_total')

    @api.depends('invoice_ids', 'invoice_count', 'order_line.invoice_lines')
    def _get_paid_total(self):
        for rec in self:
            paid_out = 0.00
            paid_in = 0.00
            if rec.invoice_ids:
                rec.invoice_ids._get_paid_total()
                paid_in = sum(inv.paid_total for inv in rec.invoice_ids if inv.type in ['out_invoice'] and inv.state not in ['draft', 'cancel']) or 0.00
                paid_out = sum(inv.paid_total for inv in rec.invoice_ids if inv.type in ['out_refund'] and inv.state not in ['draft', 'cancel']) or 0.00
            rec.paid_total = paid_in - paid_out

    @api.depends('order_line.invoice_lines')
    def _get_invoiced(self):
        super(SaleOrder, self)._get_invoiced()
        self._get_paid_total()

####################################################################################################################################
#####################################################################################################################################

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    paid_total = fields.Float('Paid Total', store=True, compute='_get_paid_total')

    @api.depends('invoice_ids', 'invoice_count', 'order_line.invoice_lines')
    def _get_paid_total(self):
        for rec in self:
            paid_out = 0.00
            paid_in = 0.00
            print("ooooooooooooooo")
            if rec.invoice_ids:
                rec.invoice_ids._get_paid_total()
                print("jjjjjjjjjjjj", rec.invoice_ids)
                paid_in = sum(inv.paid_total for inv in rec.invoice_ids if inv.type in ['in_invoice'] and inv.state not in ['draft', 'cancel']) or 0.00
                paid_out = sum(inv.paid_total for inv in rec.invoice_ids if inv.type in ['in_refund'] and inv.state not in ['draft', 'cancel']) or 0.00
            rec.paid_total = paid_in - paid_out
            print("jjjjjjjjjjjj", paid_in)
            print("jjjjjjjjjjjj", paid_out)

    @api.depends('order_line.invoice_lines.move_id')
    def _compute_invoice(self):
        super(SaleOrder, self)._compute_invoice()
        self._get_paid_total()

####################################################################################################################################
#####################################################################################################################################

class AccountMove(models.Model):
    _inherit = 'account.move'

    paid_total = fields.Float('Paid Total', store=True, compute='_get_paid_total')
    paid_state = fields.Selection([('not_paid', 'Not Paid'), ('in_paid', 'In Paid'), ('paid', 'Paid')], string='Paid State', store=True, compute='_get_paid_total')

    @api.depends('invoice_payment_state', 'state', 'line_ids', 'amount_residual')
    def _get_paid_total(self):
        for rec in self:
            paid = rec.amount_total - rec.amount_residual
            rec.paid_total = paid
            print("uuuuuu ", paid)
            if paid >= rec.amount_total:
                rec.paid_state = 'paid'
            elif paid > 0:
                rec.paid_state = 'in_paid'
            else:
                rec.paid_state = 'not_paid'

    @api.depends(
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state')
    def _compute_amount(self):
        super(AccountMove, self)._compute_amount()
        self._get_paid_total()