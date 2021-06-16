# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import float_compare, float_is_zero
from odoo.exceptions import UserError

from odoo.tests import Form

import logging
_logger = logging.getLogger(__name__)


class SaleReturnWizard(models.TransientModel):
    _name = "sale.return.wizard"

    sale_id = fields.Many2one("sale.order", string="Sale Order", domain=[("state", "=", "sale")])
    picking_id = fields.Many2one("stock.picking", string="Picking", related="sale_id.main_picking_id")
    lines = fields.One2many("return.wizard.line", "wizard_id", "Return Lines")
    journal_id = fields.Many2one("account.journal",  domain="[('type', 'in', ('bank', 'cash'))]",
                                 string="Pay off Remaining Refund")

    def _create_lines(self):
        order_line = self.sale_id.order_line
        wiz_line = self.env["return.wizard.line"]
        for line in order_line:
            wiz_line += wiz_line.create({'order_line': line.id})
        return wiz_line

    @api.onchange('sale_id')
    def _onchange_sale_id(self):
        self.update({'lines': [(5,)]})
        if self.sale_id:
            lines = self._create_lines()
            if lines:
                self.update({'lines': [(6, 0, lines.ids)]})

    # def unreconcile_paid_invoice(self, invoice):
    #     payments = self.env["account.payment"].search([("invoice_ids", "in", [invoice.id])])
    #     for payment in payments:
    #         credit_aml = payment.move_line_ids.filtered('credit')
    #         credit_aml.with_context(move_id=invoice.id).remove_move_reconcile()
    #
    # def reconcile_payment(self, invoice):
    #     payments = self.env["account.payment"].search([("invoice_ids", "in", [invoice.id])])
    #     to_reconcile = invoice.move_line_ids.filtered('debit')
    #     for payment in payments:
    #         to_reconcile += payment.move_line_ids.filtered('credit')
    #     to_reconcile.reconcile()

    def create_payment(self, refund_invoice, journal_id):
        residual = refund_invoice.amount_residual
        payment_register = Form(
            self.env['account.payment'].with_context(active_model='account.move', active_ids=refund_invoice.ids))
        payment_register.journal_id = journal_id
        payment_register.payment_method_id = self.env.ref("account.account_payment_method_manual_out")
        payment_register.amount = residual
        payment = payment_register.save()

    def adjust_refund_invoice(self, refund_invoice):
        lines = self.lines
        for reverse_line in refund_invoice.invoice_line_ids:
            matching_line = lines.filtered(lambda x: reverse_line.id in x.order_line.invoice_lines.ids)
            qty = matching_line.return_qty if matching_line else 0
            price_unit = matching_line.price_unit if matching_line else 0
            refund_invoice.write({
                'invoice_line_ids': [(1, reverse_line.id, {'price_unit': price_unit, 'quantity': qty,})]})
        refund_invoice.post()

    def get_invoice_payment_status(self, invoice):
        total = invoice.amount_total
        residual = invoice.amount_residual
        if total == residual:
            return "not_paid"
        if residual:
            return "partial_payment"
        else:
            return "paid"

    def reconcile_refund_invoice(self, refund_invoice, invoice):
        payment_status = self.get_invoice_payment_status(invoice=invoice)
        if payment_status in ('not_paid', 'partial_payment'):
            account = refund_invoice.partner_id.property_account_receivable_id
            to_reconcile = refund_invoice.line_ids.filtered(lambda l: l.account_id == account)
            to_reconcile += invoice.line_ids.filtered(lambda l: l.account_id == account)
            to_reconcile.reconcile()
        if payment_status in ('paid', 'partial_payment'):
            journal = self.journal_id
            if journal:
                self.create_payment(refund_invoice, journal)

    def refund_invoice(self, invoice):
        move_reversal = self.env['account.move.reversal'].with_context(
            active_model="account.move", active_ids=invoice.ids).create({'refund_method': 'refund'})
        reversal = move_reversal.reverse_moves()
        refund_invoice = self.env['account.move'].browse(reversal['res_id'])
        self.adjust_refund_invoice(refund_invoice)
        self.reconcile_refund_invoice(refund_invoice, invoice)
        return refund_invoice

    def stock_return(self, lines):
        picking = self.picking_id
        if picking.state != "done":
            raise UserError("The Transfer for this order is not done")

        return_form = Form(
            self.env['stock.return.picking'].with_context(active_id=picking.id, active_model='stock.picking'))
        return_wizard = return_form.save()
        for return_move in return_wizard.product_return_moves:
            matching_line = lines.filtered(lambda x: x.order_line == return_move.move_id.sale_line_id)
            qty = matching_line.return_qty  if matching_line else 0
            return_move.write({
                'quantity': qty,
                'to_refund': True
            })
        return_picking_id, pick_type_id = return_wizard._create_returns()
        return_picking = self.env['stock.picking'].browse(return_picking_id)

        return_picking.action_confirm()
        return_picking.action_assign()
        for move in return_picking.move_lines:
            move.write({'quantity_done': move.product_uom_qty})
        return_picking.action_done()
        return return_picking

    def check_lines(self):
        lines = self.lines
        prec = self.env["decimal.precision"].precision_get("Product Unit of Measure")
        wrong_lines = lines.filtered(
            lambda r: float_compare(r.ordered_qty, r.return_qty, precision_rounding=prec) == -1)
        if wrong_lines:
            raise UserError(_("You can't return more than ordered quantity"))
        lines_to_refund = lines.filtered(
            lambda r: float_compare(r.ordered_qty, r.return_qty, precision_rounding=prec) in (1, 0) and
                     r.return_qty != 0)
        return lines_to_refund

    def process_return(self):
        lines = self.check_lines()
        if lines:
            refund_invoices = self.env["account.move"]
            sale_order = self.sale_id
            return_picking = self.stock_return(lines)
            # if sale_order.invoice_status != 'invoiced':
            #     raise UserError(_("you can't return an Order that not fully invoiced"))
            invoices = lines.mapped("order_line").mapped("invoice_lines").mapped("move_id")
            invoices = invoices.filtered(lambda x: x.state == "posted")
            for invoice in invoices:
                refund_invoice = self.refund_invoice(invoice)
                refund_invoices += refund_invoice
            self.env["sale.order.return"].create({
                "name": "Return of %s" % sale_order.name,
                "sale_id": sale_order.id,
                "picking_id": self.picking_id.id,
                "return_picking_id": return_picking.id,
                "invoice_ids": invoices.ids,
                "refund_invoice_ids": refund_invoices.ids,
            })

################################################################


class SaleReturnLine(models.TransientModel):
    _name = "return.wizard.line"

    wizard_id = fields.Many2one("sale.return.wizard", string="wizard")

    order_line = fields.Many2one("sale.order.line", string="Sale Order Line")
    product_id = fields.Many2one("product.product", string="Product", related="order_line.product_id")
    ordered_qty = fields.Float("Ordered Quantity", related="order_line.qty_invoiced")
    product_uom_id = fields.Many2one('uom.uom', string='Product Unit of Measure', related="order_line.product_uom")
    price_unit = fields.Float("Price", related="order_line.price_unit")
    return_qty = fields.Float(" Quantity to Return", )

    def confirm_amount(self):
        pass

