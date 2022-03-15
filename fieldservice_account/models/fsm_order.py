# Copyright (C) 2018 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class FSMOrder(models.Model):
    _inherit = "fsm.order"

    invoice_lines = fields.Many2many(
        "account.move.line",
        "fsm_order_account_move_line_rel",
        "fsm_order_id",
        "account_move_line_id",
        string="Invoice Lines",
        copy=False,
    )
    invoice_ids = fields.Many2many(
        "account.move",
        string="Invoices",
        compute="_compute_get_invoiced",
        readonly=True,
        copy=False,
    )
    invoice_count = fields.Integer(
        string="Invoice Count",
        compute="_compute_get_invoiced",
        readonly=True,
        copy=False,
    )
    bill_ids = fields.Many2many(
        "account.move",
        string="Bills",
        compute="_compute_get_billed",
        readonly=True,
        copy=False,
    )
    bill_count = fields.Integer(
        string="Bill Count", compute="_compute_get_billed", readonly=True, copy=False,
    )

    @api.depends("invoice_lines")
    def _compute_get_invoiced(self):
        for order in self:
            invoices = order.invoice_lines.mapped("move_id").filtered(
                lambda r: r.type in ("out_invoice", "out_refund")
            )
            order.invoice_ids = invoices
            order.invoice_count = len(invoices)

    def action_view_invoices(self):
        action = self.env.ref("account.action_move_out_invoice_type").read()[0]
        invoices = self.mapped("invoice_ids")
        if len(invoices) > 1:
            action["domain"] = [("id", "in", invoices.ids)]
        elif invoices:
            action["views"] = [(self.env.ref("account.view_move_form").id, "form")]
            action["res_id"] = invoices.ids[0]
        return action

    @api.depends("invoice_lines")
    def _compute_get_billed(self):
        for order in self:
            bills = order.invoice_lines.mapped("move_id").filtered(
                lambda r: r.type in ("in_invoice", "in_refund")
            )
            order.bill_ids = bills
            order.bill_count = len(bills)

    def action_view_bills(self):
        action = self.env.ref("account.action_move_in_invoice_type").read()[0]
        bills = self.mapped("bill_ids")
        if len(bills) > 1:
            action["domain"] = [("id", "in", bills.ids)]
        elif bills:
            action["views"] = [(self.env.ref("account.view_move_form").id, "form")]
            action["res_id"] = bills.ids[0]
        return action
