from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    auto_pick_po = fields.Boolean(string='Auto Picking (PO)')
    auto_pick_so = fields.Boolean(string='Auto Picking (SO)')

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        parameter_obj = self.env['ir.config_parameter'].sudo()
        parameter_obj.set_param('fin_app.auto_pick_po', bool(self.auto_pick_po))
        parameter_obj.set_param('fin_app.auto_pick_so', bool(self.auto_pick_so))


    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        parameter_obj = self.env['ir.config_parameter'].sudo()
        auto_pick_po = parameter_obj.get_param('fin_app.auto_pick_po')
        auto_pick_so = parameter_obj.get_param('fin_app.auto_pick_so')

        res.update(
            auto_pick_po=bool(auto_pick_po), auto_pick_so=bool(auto_pick_so),
        )
        return res
