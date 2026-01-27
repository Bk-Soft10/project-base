# -*- coding: utf-8 -*-

from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        print("session_info called ✅")

        session_info = super().session_info()

        user = self.env.user
        current_user_id = user.id

        user_id = self.env['res.users'].browse(current_user_id)

        max_attachment_size_mb = None

        if user_id and user_id.user_select_attachment_size_unit and user.users_general_size_limit_attachment > 0:
            unit = user_id.user_select_attachment_size_unit
            size = user_id.users_general_size_limit_attachment


            if unit == 'kb':
                max_attachment_size_mb = size * 1024
            else:
                max_attachment_size_mb = size * 1024 * 1024

        else:
            enable_general_limit = self.env['ir.config_parameter'].sudo().get_param(
                'pys_attachment_size_limitation.enable_general_size_limit_attachment',
                False
            )

            if enable_general_limit:

                unit = self.env["ir.config_parameter"].sudo().get_param(
                    "pys_attachment_size_limitation.select_attachment_size_unit",
                )

                size = int(
                    self.env["ir.config_parameter"].sudo().get_param(
                        "pys_attachment_size_limitation.general_size_limit_attachment",
                        0
                    )
                )

                if unit and size > 0:
                    if unit == 'kb':
                        max_attachment_size_mb = size * 1024
                    else:
                        max_attachment_size_mb = size * 1024 * 1024


        session_info["max_attachment_size"] = max_attachment_size_mb


        print("max_attachment_size:::::::::::", session_info["max_attachment_size"])
        return session_info
