from odoo import models, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def create(self, vals):
        record = super().create(vals)

        for rec in record:
            other_model = self.env["sh.user.push.notification"].create_user_notification(
                self.env.user,
                "Sale Order ------------->",
                "Sale Order Created Successfully  ---------->",
                self._name,
                rec["id"]
            )
        params = {}
        self.env.user._bus_send("sh_notif", params)
        return record
