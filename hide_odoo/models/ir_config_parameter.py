
from odoo import api, models
from odoo.tools.translate import _

PARAMS = [
    ("hide_odoo.system_name", _("Software")),
]


def get_debranding_parameters_env(env):
    res = {}
    for param, default in PARAMS:
        value = env["ir.config_parameter"].sudo().get_param(param, default)
        res[param] = value.strip()
    return res


class IrConfigParameter(models.Model):
    _inherit = "ir.config_parameter"

    @api.model
    def get_debranding_parameters(self):
        return get_debranding_parameters_env(self.env)

    @api.model
    def create_debranding_parameters(self):
        for param, default in PARAMS:
            if not self.env["ir.config_parameter"].sudo().get_param(param):
                self.env["ir.config_parameter"].sudo().set_param(param, default or " ")
